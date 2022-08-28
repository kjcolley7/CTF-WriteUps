module top();
    reg clock,reset;
    wire [11:0] instruction;
    wire [7:0] pc,dataWriteAddr,dataWriteVal,dataReadAddr,valueFromData;
    wire writeEnable;
    string flag;
    integer z;

    initial forever begin
        clock = 0; #5;
        clock = 1; #5;
    end
    
    initial begin
        #1;
        flag = "maple{testflag}";
        for (i=0; i< flag.len(); i++)
            DataMem.datatxt[i+140] = flag[i];
        reset = 1;
        #10;
        reset = 0;
        #500000;
        if (DataMem.datatxt[135] == 2)
            $display("You are winner!");
        else
            $display("Try again.");
        $finish();
    end

    Cpu cpu(clock,reset,
        instruction,pc,
        dataWriteAddr,dataWriteVal,writeEnable,
        dataReadAddr,valueFromData);
    
    Ram #(8,8,"data.txt") DataMem(clock,dataReadAddr,dataWriteAddr,writeEnable,dataWriteVal,valueFromData);
    Ram #(12,8,"prog.txt") ProgMem(clock,pc,8'b0,1'b0,12'b0,instruction);
endmodule

module Ram(clock,readAddr,writeAddr,writeEnable,dataWriteVal,outDataRead);
  parameter wordBits = 32; 
  parameter addressBits = 4;
  parameter datafile = "data.txt";

  input clock;
  input [addressBits-1:0] readAddr, writeAddr;
  input writeEnable;
  input [wordBits-1:0] dataWriteVal;
  output logic [wordBits-1:0] outDataRead;

  reg [wordBits-1:0] datatxt [2**addressBits-1:0];

  initial $readmemh(datafile, datatxt);

  always @ (posedge clock) begin
    if (writeEnable)
      datatxt[writeAddr] <= dataWriteVal;
    outDataRead <= datatxt[readAddr];
  end 
endmodule

module Cpu(clock,reset,
        instruction,pc,
        dataWriteAddr,dataWriteVal,writeEnable,
        dataReadAddr,valueFromData);

    input clock, reset;
    input [11:0] instruction;
    input [7:0] valueFromData;
    output logic [7:0] pc;
    output wire [7:0] dataWriteAddr,dataReadAddr,dataWriteVal;
    output logic writeEnable;

    wire [7:0] operand1,operand2;

    logic dataStackEnable,callStackEnable;
    logic [2:0] dataStackOp,callStackOp;
    logic [2:0] aluOp;

    wire [3:0] opcode;
    wire [7:0] imm8,jumpTarget,dataToPush,poppedReturnAddress,pushReturnAddress;
    logic isReturn,pushImmediate,pushAluResult,jumpCond,updateJumpCond;
    logic [7:0] nextPC;

    typedef enum {pcReset,pcJump,pcNext,pcAgain} PCUpdateMode;
    PCUpdateMode pcUpdateMode;

    enum {execNo,execYes} shouldExecute;

    /*
    module Execute(clock,reset,
                pushAluResult,
                poppedReturnAddress,
                aluOp,zeroFlag,
                dataStackEnable,callStackEnable,
                dataStackOp,callStackOp,
                dataToPush,pushReturnAddress,
                operand1,operand2)
    */
    Execute ex(clock,reset,
                pushAluResult,
                poppedReturnAddress,
                aluOp,zeroFlag,
                dataStackEnable,callStackEnable,
                dataStackOp,callStackOp,
                dataToPush,pushReturnAddress,
                operand1,operand2);

    assign opcode = instruction[11:8];
    assign imm8 = instruction[7:0];
    assign jumpTarget = isReturn == 0 ? imm8 : poppedReturnAddress;
    assign dataWriteAddr = operand2;
    assign dataReadAddr = operand1;
    assign dataToPush = pushImmediate == 1 ? imm8 : valueFromData;
    
    assign dataWriteVal = operand1;
    assign pushReturnAddress = pc + 1;
    
    always_comb begin
        pushAluResult = 1'b0;
        dataStackEnable = 1'b0;
        callStackEnable = 1'b0;
        dataStackOp = 3'b0;
        callStackOp = 3'b0;
        pcUpdateMode = pcNext;
        isReturn = 1'b0;
        pushImmediate = 1'b1;
        writeEnable = 1'b0;
        updateJumpCond = 1'b0;
        if (shouldExecute == execYes) begin
        casez(opcode)
            4'b0???: begin // 0x0-0x7
                    if (opcode != 7) begin
                        // 0x0-0x6
                        pushAluResult = 1'b1;
                        aluOp = opcode[2:0];
                        dataStackEnable = 1'b1;
                        dataStackOp = 3'd3;
                        updateJumpCond = 1'b1;
                    end else begin
                        // 0x7 aka pop
                        dataStackEnable = 1'b1;
                        dataStackOp = 3'd4;
                        end
                    end
            4'd8: begin // 0x8 aka jmp
                    pcUpdateMode = pcJump;
                    isReturn = 1'b0;
                    end
            4'd9: begin // 0x9 aka call
                    pcUpdateMode = pcJump;
                    callStackEnable = 1'b1;
                    callStackOp = 3'd0;
                    isReturn = 1'b0;
                    end
            4'd10: begin // 0xa aka ret
                    pcUpdateMode = pcJump;
                    callStackEnable = 1'b1;
                    callStackOp = 3'd4;
                    isReturn = 1'b1;
                    end
            4'd11: begin // 0xb aka jzr
                    isReturn = 1'b0;
                    if(jumpCond)
                        pcUpdateMode = pcJump;
                    else
                        pcUpdateMode = pcNext;
                    end
            4'd12: begin // 0xc aka push
                    pushAluResult = 1'b0;
                    dataStackEnable = 1'b1;
                    dataStackOp = 3'b0;
                    end
            4'd13: begin // 0xd aka ldm
                    dataStackOp = 3'd1;
                    pushAluResult = 1'b0;
                    pushImmediate = 1'b0;
                    dataStackEnable = 1'b1;
                    end
            4'd14: begin // 0xe aka stm
                    writeEnable = 1'b1;
                    dataStackOp = 3'd2;
                    dataStackEnable = 1'b1;
            end
            4'd15: pcUpdateMode = pcAgain;
        endcase
        end
    end

    
    always_comb begin
        case(pcUpdateMode)
            pcReset: nextPC = 8'b0;
            pcJump: nextPC = jumpTarget;
            pcNext: nextPC = pc + 1;
            pcAgain: nextPC = pc;
            default: nextPC = 8'bz;
        endcase
    end

    always_ff @(posedge clock) begin
        if (reset) begin
            pc <= 8'b0;
        end
        else begin
            if (shouldExecute == execYes)
                pc <= nextPC;
            if (updateJumpCond == 1)
                jumpCond = zeroFlag;
        end
    end

    always_ff @(posedge clock) begin
        if (reset)
            shouldExecute <= execNo;
        else begin
            case(shouldExecute)
                execNo: shouldExecute <= execYes;
                execYes: shouldExecute <= execNo;
            endcase
        end
    end
endmodule

module Execute(clock,reset,
                pushAluResult,
                poppedReturnAddress,
                aluOp,zeroFlag,
                dataStackEnable,callStackEnable,
                dataStackOp,callStackOp,
                dataToPush,pushReturnAddress,
                operand1,operand2);
    input clock,reset,pushAluResult,dataStackEnable,callStackEnable;
    input [7:0] dataToPush,pushReturnAddress;
    input [2:0] dataStackOp,callStackOp;
    output logic [7:0] poppedReturnAddress,operand1,operand2;
    input [2:0] aluOp;
    output wire zeroFlag;
    
    wire [7:0] pushValue, aluResult,aluArg1, aluArg2, dontcare;

    assign pushValue = pushAluResult == 0 ? dataToPush : aluResult;
    assign operand1 = aluArg1;
    assign operand2 = aluArg2;

    Stack #(10) dataStack(.clock(clock),.reset(reset),
                        .pushValue(pushValue),
                        .poppedHigh(aluArg1),.poppedLow(aluArg2),
                        .stackOp(dataStackOp),.stackEnable(dataStackEnable));

    Stack #(10) callStack(.clock(clock),.reset(reset),
                            .pushValue(pushReturnAddress),
                            .poppedHigh(poppedReturnAddress),.poppedLow(dontcare),
                            .stackOp(callStackOp),.stackEnable(callStackEnable));

// module Alu(opA,opB,aluOp,aluResult,zeroFlag)
    Alu Alu(aluArg1,aluArg2,aluOp,aluResult,zeroFlag);
endmodule

module Stack(clock,reset,pushValue,poppedHigh,poppedLow,stackOp,stackEnable);
    input clock,reset,stackEnable;
    
    input [7:0] pushValue;
    output [7:0] poppedHigh,poppedLow;
    input [2:0] stackOp;

    parameter stackBytes = 16;
    logic [7:0] stackMem [2**stackBytes-1:0];
    logic [stackBytes-1:0] stackPointer;


    always_ff @(posedge clock) begin
        if (reset == 1) begin
            stackPointer <= 0;
        end else if (stackEnable ==1) begin
            case (stackOp)
                3'd0: begin
                        stackMem[stackPointer+1] <= pushValue;
                        stackPointer <= stackPointer + 1;
                end
                3'd1: stackMem[stackPointer]<=pushValue;
                3'd2: stackPointer <= stackPointer - 2;
                3'd3: begin 
                        stackPointer <= stackPointer - 1; 
                        stackMem[stackPointer-1] <= pushValue;
                end
                3'd4: stackPointer <= stackPointer - 1;
            endcase
        end
    end

    assign {poppedHigh,poppedLow} = {stackMem[stackPointer],stackMem[stackPointer-1]};

endmodule

module Alu(opA,opB,aluOp,aluResult,zeroFlag);
    input [7:0] opA,opB;
    output logic [7:0] aluResult;
    input [2:0] aluOp;
    output zeroFlag;

    assign zeroFlag = aluResult == 0 ? 1'b1 : 1'b0;

    always_comb begin
        case (aluOp)
            3'd0: aluResult = opA + opB;
            3'd1: aluResult = opA - opB;
            3'd2: aluResult = opA ^ opB;
            3'd3: aluResult = opA & opB;
            3'd4: aluResult = opA | opB;
            3'd5: aluResult = opA << opB;
            3'd6: aluResult = opA >> opB;
            default: aluResult = 8'bz;
        endcase
    end
endmodule
