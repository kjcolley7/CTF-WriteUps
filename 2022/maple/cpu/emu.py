#!/usr/bin/env python3
"""
0 (0): HALT

1 (1): NOP

2 (1): MOVcc b, a
	# ra rb
	# valA = ra
	# valB = rb
	# store valE -> rb
	# NOMEM
	# aluB = 0
	# aluA = valA
	# aluOp = ALU_ADD
	# rb = 0 + ra

3 (5): MOVI b, imm64
	# rb
	# store valE -> rb
	# NOMEM
	# aluB = 0
	# aluA = imm64
	# aluOp = ALU_ADD
	# rb = 0 + imm64

4 (5): STR a, [b + imm64]
	# ra rb
	# valA = ra
	# valB = rb
	# addr = valE
	# data = valA
	# MEMWRITE
	# aluB = valB
	# aluA = imm64
	# aluOp = ALU_ADD
	# *(b + imm64) = a

5 (5): LDR a, [b + imm64]
	# ra rb
	# valB = rb
	# store valM -> ra
	# addr = valE
	# MEMREAD
	# aluB = valB
	# aluA = imm64
	# aluOp = ALU_ADD
	# ra = *(rb + imm64)

6 (1): alu b, a
	# ra rb
	# valA = ra
	# valB = rb
	# store valE -> rb
	# NOMEM
	# aluB = valB
	# aluA = valA
	# aluOp = op
	# rb = rb op ra

7 (5): Jcc imm64
	# NOMEM
	# NOALU, iFn is instead a condition
	# if cond: goto imm64

8 (5): CALL b, imm64
	# rb
	# valA = ra #WTF
	# valB = rb
	# store valE -> rb
	# addr = valE
	# data = valP
	# MEMWRITE
	# aluB = valB
	# aluA = 4
	# aluOp = ALU_SUB
	# rb -= 4
	# *rb = return address
	# goto imm64
	# aka
	# rb.push(return address)
	# goto imm64

9 (1): RET b
	# rb
	# valA = rb
	# valB = rb
	# store valE -> rb
	# addr = valA
	# MEMREAD
	# aluB = valB
	# aluA = 4
	# aluOp = ALU_ADD
	# goto *rb
	# rb += 4
	# aka
	# goto rb.pop()

A (1): PUSH a, [b]
	# ra rb
	# valA = ra
	# valB = rb
	# store valE -> rb
	# addr = valE
	# data = valA
	# MEMWRITE
	# aluB = valB
	# aluA = 4
	# aluOp = ALU_SUB
	# rb -= 4
	# *rb = ra
	# aka
	# rb.push(ra)

B (1): POP a, [b]
	# ra rb
	# valA = rb
	# valB = rb
	# store valM -> ra
	# store valE -> rb
	# addr = valA
	# MEMREAD
	# aluB = valB
	# aluA = 4
	# aluOp = ALU_ADD
	# ra = *rb
	# rb += 4
	# aka
	# ra = rb.pop()
"""

# 0 (0): HALT
# 1 (1): NOP
# 2 (1): MOVcc b, a
# 3 (5): MOVI b, imm64
# 4 (5): STR a, [b + imm64]
# 5 (5): LDR a, [b + imm64]
# 6 (1): alu b, a
# 7 (5): Jcc imm64
# 8 (5): CALL b, imm64
# 9 (1): RET b
# A (1): PUSH a, [b]
# B (1): POP a, [b]
_INSNS = (
	"HALT",
	"NOP",
	"MOVcc",
	"MOVI",
	"STR",
	"LDR",
	"alu",
	"Jcc",
	"CALL",
	"RET",
	"PUSH",
	"POP",
	"illC",
	"illD",
	"illE",
	"illF"
)

OP_HALT = 0
OP_NOP  = 1
OP_MOV  = 2
OP_MOVI = 3
OP_STR  = 4
OP_LDR  = 5
OP_ALU  = 6
OP_JCC  = 7
OP_CALL = 8
OP_RET  = 9
OP_PUSH = 0xA
OP_POP  = 0xB


_REGS = (
	"eax",
	"ecx",
	"edx",
	"ebx",
	"esp",
	"ebp",
	"esi",
	"edi",
	
	"rto",
	"r9",
	"r10",
	"r11",
	"r12",
	"r13",
	"r14",
	None
)

R_EAX = 0
R_ECX = 1
R_EDX = 2
R_EBX = 3
R_ESP = 4
R_EBP = 5
R_ESI = 6
R_EDI = 7

R_RTO = 8
R_R9  = 9
R_R10 = 10
R_R11 = 11
R_R12 = 12
R_R13 = 13
R_R14 = 14


_HAS_IMM = set([
	OP_MOVI,
	OP_STR,
	OP_LDR,
	OP_JCC,
	OP_CALL
])


def _read64(mem, addr):
	return (
		(mem[addr] << 48)
		| (mem[addr+1] << 32)
		| (mem[addr+2] << 16)
		| mem[addr+3]
	)

def _write64(mem, addr, value):
	mem[addr] = (value >> 48) & 0xffff
	mem[addr+1] = (value >> 32) & 0xffff
	mem[addr+2] = (value >> 16) & 0xffff
	mem[addr+3] = value & 0xffff

def _decode(mem, pc):
	opfnregs = mem[pc]
	
	op = opfnregs >> 12
	fn = (opfnregs >> 8) & 0x0f
	regs = opfnregs & 0x00ff
	ra = regs >> 4
	rb = regs & 0x0f
	
	imm = None
	if op in _HAS_IMM:
		imm = _read64(mem, pc + 1)
	
	return (op, fn, ra, rb, imm)


_ALU = (
	"add",
	"sub",
	"and",
	"xor",
	"mul",
	"div",
	"mod",
	"shl",
	"shr"
)

_ALUOP = (
	"+",
	"-",
	"&",
	"^",
	"*",
	"/",
	"%",
	"<<",
	">>"
)

ALU_ADD = 0x0
ALU_SUB = 0x1
ALU_AND = 0x2
ALU_XOR = 0x3
ALU_MUL = 0x4
ALU_DIV = 0x5
ALU_MOD = 0x6
ALU_SHL = 0x7
ALU_SHR = 0x8

_MASK64 = (1 << 64) - 1

def _alu(op, a, b):
	if op == ALU_ADD:
		e = b + a
	elif op == ALU_SUB:
		e = b - a
	elif op == ALU_AND:
		e = b & a
	elif op == ALU_XOR:
		e = b ^ a
	elif op == ALU_MUL:
		e = b * a
	elif op == ALU_DIV:
		e = b // a
	elif op == ALU_MOD:
		e = b % a
	elif op == ALU_SHL:
		e = (b << (a & 0x3f)) & _MASK64
	elif op == ALU_SHR:
		e = b >> (a & 0x3f)
	else:
		e = 0
	
	if e & ~_MASK64:
		o = True
	else:
		o = False
	
	e &= _MASK64
	
	z = not bool(e)
	s = bool(e & (1 << 63))
	
	return (e, z, s, o)


_COND = (
	None,
	"le",
	"lt",
	"eq",
	"ne",
	"ge",
	"gt"
)

def _cond2str(fn, df):
	s = None
	if fn < len(_COND):
		s = _COND[fn]
	
	return s or df

COND_AL = 0
COND_LE = 1
COND_LT = 2
COND_EQ = 3
COND_NE = 4
COND_GE = 5
COND_GT = 6

def _evalcond(cond, z, s, o):
	so = s ^ o
	
	if cond == COND_LE:
		return z or so
	elif cond == COND_LT:
		return so
	elif cond == COND_EQ:
		return z
	elif cond == COND_NE:
		return not z
	elif cond == COND_GE:
		return not so
	elif cond == COND_GT:
		return not (z or so)
	else:
		return True


# 0 (0): HALT
# 1 (1): NOP
# 2 (1): MOVcc b, a
# 3 (5): MOVI b, imm64
# 4 (5): STR a, [b + imm64]
# 5 (5): LDR a, [b + imm64]
# 6 (1): alu b, a
# 7 (5): Jcc imm64
# 8 (5): CALL b, imm64
# 9 (1): RET b
# A (1): PUSH a, [b]
# B (1): POP a, [b]
def disassemble_one(mem, pc):
	op, fn, ra, rb, imm = _decode(mem, pc)
	
	def pr(s):
		print("%#x: %s" % (pc, s))
	
	a = _REGS[ra]
	b = _REGS[rb]
	
	if op == OP_HALT:
		pr("halt")
	elif op == OP_NOP:
		pr("nop")
	elif op == OP_MOV:
		pr("mov%s %s, %s" % (_cond2str(fn, ""), b, a))
	elif op == OP_MOVI:
		pr("movi %s, %#x" % (b, imm))
	elif op == OP_STR:
		pr("str %s, [%s + %#x]" % (a, b, imm))
	elif op == OP_LDR:
		pr("ldr %s, [%s + %#x]" % (a, b, imm))
	elif op == OP_ALU:
		pr("%s %s, %s" % (_ALU[fn], b, a))
	elif op == OP_JCC:
		pr("j%s 0x%x" % (_cond2str(fn, "mp"), imm))
	elif op == OP_CALL:
		pr("call %s, 0x%x" % (b, imm))
	elif op == OP_RET:
		pr("ret %s" % b)
	elif op == OP_PUSH:
		pr("push %s, [%s]" % (a, b))
	elif op == OP_POP:
		pr("pop %s, [%s]" % (a, b))
	else:
		raise ValueError("Illegal opcode: 0x%X" % op)
	
	pc += 5 if imm is not None else 1
	return pc

def disassemble(mem, pc=0, count=None):
	try:
		while True:
			if count is not None:
				if count == 0:
					break
				
				count -= 1
			
			pc = disassemble_one(mem, pc)
	except ValueError as e:
		print("0x%x: %s" % (pc, e))
	except IndexError:
		pass


class Halted(Exception):
	pass


class CPU:
	def __init__(self):
		self.mem = [0] * (1 << 24)
		self.should_log = False
		self.reset()
		
		self.breakpoints = set([])
	
	def copyin(self, data, addr=0):
		copysize = min(len(data), len(self.mem) - addr)
		self.mem[addr:addr+copysize] = data[:copysize]
	
	def reset(self):
		self.pc = 0
		self.zf = True
		self.sf = False
		self.of = False
		self.regs = [0] * 15
	
	# sp -= 4
	# *sp = value
	def _push(self, sp, value):
		addr = self.regs[sp] - 4
		self.regs[sp] = addr
		_write64(self.mem, addr, value)
	
	# ret = *sp
	# sp += 4
	def _pop(self, sp):
		addr = self.regs[sp]
		self.regs[sp] = addr + 4
		return _read64(self.mem, addr)
	
	# 0 (0): HALT
	# 1 (1): NOP
	# 2 (1): MOV b, a
	# 3 (5): MOVI b, imm64
	# 4 (5): STR a, [b + imm64]
	# 5 (5): LDR a, [b + imm64]
	# 6 (1): alu b, a
	# 7 (5): Jcc imm64
	# 8 (5): CALL b, imm64
	# 9 (1): RET b
	# A (1): PUSH a, [b]
	# B (1): POP a, [b]
	def step(self):
		op, fn, ra, rb, imm = _decode(self.mem, self.pc)
		mnem = _INSNS[op]
		
		nextpc = self.pc + 1
		if imm is not None:
			nextpc += 4
		
		a = _REGS[ra]
		b = _REGS[rb]
		
		if op == OP_HALT:
			self.log("halt")
			raise Halted()
		elif op == OP_NOP:
			self.log("nop")
		elif op == OP_MOV:
			if _evalcond(fn, self.zf, self.sf, self.of):
				value = self.regs[ra]
				self.log("mov%s %s, %s (cond TRUE, %#x)" % (_cond2str(fn, ""), b, a, value))
				self.regs[rb] = value
			else:
				self.log("mov%s %s, %s (cond FALSE, %#x)" % (_cond2str(fn, ""), b, a, value))
		elif op == OP_MOVI:
			self.log("movi %s, %#x" % (b, imm))
			self.regs[rb] = imm
		elif op == OP_STR:
			addr = self.regs[rb] + imm
			data = self.regs[ra]
			self.log("str %s, [%s + %#x] (*0x%x = %#x)" % (a, b, imm, addr, data))
			_write64(self.mem, addr, data)
		elif op == OP_LDR:
			addr = self.regs[rb] + imm
			data = _read64(self.mem, addr)
			self.log("ldr %s, [%s + %#x] (%#x <= *0x%x)" % (a, b, imm, data, addr))
			self.regs[ra] = data
		elif op == OP_ALU:
			va = self.regs[ra]
			vb = self.regs[rb]
			e, z, s, o = _alu(fn, va, vb)
			self.log("%s %s, %s (%#x %s %#x = %#x [%s%s%s])" % (
				_ALU[fn], b, a, vb, _ALUOP[fn], va, e,
				"Z" if z else "z",
				"S" if s else "s",
				"O" if o else "o"
			))
			
			self.regs[rb] = e
			self.zf = z
			self.sf = s
			self.of = o
		elif op == OP_JCC:
			if _evalcond(fn, self.zf, self.sf, self.of):
				self.log("j%s 0x%x (cond TRUE)" % (_cond2str(fn), imm))
				nextpc = imm
			else:
				self.log("j%s 0x%x (cond FALSE)" % (_cond2str(fn), imm))
		elif op == OP_CALL:
			self._push(rb, nextpc)
			self.log("call %s, 0x%x (stack = 0x%x, ret = 0x%x)" % (b, imm, self.regs[rb], nextpc))
			nextpc = imm
		elif op == OP_RET:
			nextpc = self._pop(rb)
			self.log("ret %s (stack = 0x%x, ret = 0x%x)" % (b, self.regs[rb], nextpc))
		elif op == OP_PUSH:
			va = self.regs[ra]
			self._push(rb, va)
			self.log("push %s, [%s] (stack = 0x%x, pushed = %#x)" % (a, b, self.regs[rb], va))
		elif op == OP_POP:
			popped = self._pop(rb)
			self.regs[ra] = popped
			self.log("pop %s, [%s] (stack = 0x%x, popped = %#x)" % (a, b, self.regs[rb], popped))
		else:
			raise ValueError("Illegal instruction: %s" % mnem)
		
		self.pc = nextpc
	
	def run(self):
		try:
			while True:
				self.step()
				if self.pc in self.breakpoints:
					print("Hit breakpoint at %02X" % self.pc)
					return
		except Halted:
			return
		except ValueError as e:
			print(e)
	
	def log(self, s):
		if not self.should_log:
			return
		
		print("%02X: %s" % (self.pc, s))
	
	def context(self):
		print("Register state:")
		print("PC: %02X" % self.pc)
		for i, val in enumerate(self.regs):
			print("%s: %#x" % (_REGS[i], val))
		
		print("\nNext instructions:")
		disassemble(self.mem, self.pc, 5)
		print("")
	
	def debugger(self):
		lastline = "help"
		self.context()
		
		while True:
			line = input("(dbg) ")
			if not line:
				line = lastline
			
			lastline = line
			args = line.split(" ")
			cmd = args[0]
			
			if cmd in ("si", "step"):
				self.step()
				self.context()
			elif cmd in ("c", "cont", "continue"):
				self.run()
				self.context()
			elif cmd in ("b", "break"):
				self.breakpoints.add(int(args[1], 16))
			elif cmd in ("ctx", "ctxt", "context"):
				self.context()
			# elif cmd in ("mem", "xxd", "hexdump"):
			# 	self.showmem()
			elif cmd in ("q", "quit", "exit"):
				break
			# elif cmd == "watchmem":
			# 	self.watchmem = not self.watchmem
			elif cmd == "log":
				self.should_log = not self.should_log
			elif cmd in ("h", "help", "?"):
				print("Commands: step, continue, break, context")
			else:
				print("Unknown command '%s'" % cmd)


def load_raw(filename):
	data16 = []
	
	with open(filename) as fp:
		text = fp.read()
	
	for line in text.split("\n"):
		if not line or line == "v2.0 raw":
			continue
		
		for word in line.split(" "):
			if not word:
				continue
			
			data16.append(int(word, 16))
	
	return data16


def main():
	prog = load_raw("flag-checker-v5.bin")
	# disassemble(prog)
	# return
	
	FLAG_ADDRESS = 0xf1a9
	
	# maple{F1A9_F33D_BAC04_777}
	FLAG1 = 0xf1a9
	FLAG2 = 0xf33d
	FLAG3 = 0xbac0
	FLAG4 = 0x4777
	FLAG = (FLAG1 << 48) | (FLAG2 << 32) | (FLAG3 << 16) | FLAG4
	_write64(prog, FLAG_ADDRESS, FLAG)
	
	cpu = CPU()
	cpu.copyin(prog)
	
	# cpu.should_log = True
	try:
		# cpu.run()
		cpu.debugger()
	except Halted:
		print("Program halted")
	except ValueError as e:
		print(e)


if __name__ == "__main__":
	main()
