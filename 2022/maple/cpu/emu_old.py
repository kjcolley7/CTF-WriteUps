"""
0 (0): HALT

1 (1): NOP

2 (1): MOV b, a
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
	# *(rb - 4) = return address
	# rb -= 4
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
	# goto *(rb + 4)
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
	# *(rb - 4) = ra
	# rb -= 4
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
	# ra = *(rb + 4)
	# rb += 4
	# aka
	# ra = rb.pop()
"""

MASK64 = 0xffffffffffffffff

# 64-bit first_word: fw
# 16-bit second_word: sw
# iCd = opcode
# IFn = func
def _fetch(pc, fw, sw):
	opfunc = fw >> 56
	func = opfunc & 0x0f
	opc = opfunc >> 4
	regpair = (fw >> 48) & 0xff
	
	# mux1
	if opc in (0x3, 0x8, 0x9):
		regs = 0xf0 | (regpair & 0x0f)
	elif opc in (0x2, 0x4, 0x5, 0x6, 0xA, 0xB):
		regs = regpair
	else:
		regs = 0xff
	
	ra = (regs >> 4) & 0xf
	rb = regs & 0xf
	
	# mux2
	if opc in (0x3, 0x4, 0x5, 0x7, 0x8):
		valC = ((fw << 16) & MASK64) | sw
	else:
		valC = MASK64
	
	# mux3
	if opc in (0x1, 0x2, 0x6, 0x9, 0xA, 0xB):
		valP = pc + 1
	elif opc in (0x3, 0x4, 0x5, 0x7, 0x8):
		valP = pc + 5
	else:
		valP = pc + 0
	
	return (opc, func, ra, rb, valC, valP)


def _decode(opcode, ra, rb):
	# mux1
	elif opcode in (0x2, 0x4, 0x6, 0x8, 0xA):
		# Why is 0x8 here? _fetch sets ra to 0xf for opcode 0x8...
		srcA = ra
	elif opcode in (0x9, 0xB):
		srcA = rb
	else:
		srcA = 0xF
	
	# mux2
	if opcode in (0x2, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB):
		srcB = rb
	else:
		srcB = 0xF
	
	# mux3
	if opcode in (0x2, 0x3, 0x6, 0x8, 0x9, 0xA, 0xB):
		dstE = rb
	else:
		dstE = 0xF
	
	# mux4
	if opcode in (0x5, 0xB):
		dstM = ra
	else:
		dstM = 0xF
	
	return (srcA, srcB, dstE, dstM)


ALU_ADD = 0x0
ALU_SUB = 0x1
ALU_AND = 0x2
ALU_XOR = 0x3
ALU_MUL = 0x4
ALU_DIV = 0x5
ALU_MOD = 0x6
ALU_SHL = 0x7
ALU_SHR = 0x8

def _alu(a, b, func):
	if func == ALU_ADD:
		e = b + a
	elif func == ALU_SUB:
		e = b - a
	elif func == ALU_AND:
		e = b & a
	elif func == ALU_XOR:
		e = b ^ a
	elif func == ALU_MUL:
		e = b * a
	elif func == ALU_DIV:
		e = b / a
	elif func == ALU_MOD:
		e = b % a
	elif func == ALU_SHL:
		e = (b << (a & 0x3f)) & MASK64
	elif func == ALU_SHR:
		e = b >> (a & 0x3f)
	else:
		e = 0
	
	if e & ~MASK64:
		o = True
	else:
		o = False
	
	e &= MASK64
	
	z = not bool(e)
	s = bool(e & (1 << 63))
	
	return (e, z, s, o)


COND_AL = 0
COND_LE = 1
COND_LT = 2
COND_EQ = 3
COND_NE = 4
COND_GE = 5
COND_GT = 6

def _branch(opcode, z, s, o, func):
	if opcode not in (0x2, 0x7):
		return True
	
	so = s ^ o
	
	if func == COND_LE:
		return z or so
	elif func == COND_LT:
		return so
	elif func == COND_EQ:
		return z
	elif func == COND_NE:
		return not z
	elif func == COND_GE:
		return not so
	elif func == COND_GT:
		return not (z or so)
	else:
		return True


def _memory(opcode, e, a, p):
	# mux1
	if opcode in (0x4, 0x5, 0x8, 0xA):
		# Computed memory address
		addr = e
	elif opcode in (0x9, 0xB):
		# Absolute memory address
		addr = a
	else:
		addr = 0
	
	# mux2
	if opcode in (0x4, 0xA):
		# Write value from register
		data = a
	elif opcode == 0x8:
		# Write nextPC (return address)
		data = p
	else:
		data = None
	
	return (addr, data)


def _pcupdate(m, p, c, opcode, should_branch):
	if opcode == 0x7: #Jcc
		return c if should_branch else p
	elif opcode == 0x8: #CALL
		return c
	elif opcode == 0x9: #RET
		# TODO: The component uses a register. Does this need to be delayed by one cycle?
		return m


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

class CPU:
	def __init__(self):
		self.mem = [0] * (1 << 24)
		self.reset()
	
	def copyin(self, data, addr=0):
		self.mem[addr:len(self.mem)] = data[:len(self.mem) - addr]
	
	def reset(self):
		self.pc = 0
		self.zf = True
		self.sf = False
		self.of = False
		self.regs = [0] * 15
	
	def _execute(self, opcode, a, b, c, func):
		# mux1 (aluA)
		if opcode in (0x2, 0x6):
			aluA = a
		elif opcode in (0x3, 0x4, 0x5, 0x7):
			aluA = c
		elif opcode in (0x8, 0x9, 0xA, 0xB):
			aluA = 4
		else:
			aluA = 0
		
		# mux2 (aluB)
		if opcode in (0x4, 0x5, 0x6, 0x8, 0x9, 0xA, 0xB):
			aluB = b
		else:
			aluB = 0
		
		# mux3 (aluFunc):
		if opcode == 0x6:
			aluFunc = func
		elif opcode in (0x8, 0xA):
			aluFunc = ALU_SUB
		else:
			aluFunc = ALU_ADD
		
		# Emulate ALU_1 component
		e, z, s, o = _alu(aluA, aluB, aluFunc)
		
		# Should set flags?
		if opcode == 0x6:
			self.zf = z
			self.sf = s
			self.of = o
		
		# Emulate Branch_1 component
		return _branch(opcode, self.zf, self.sf, self.of, func)
	
	def getreg(self, regnum):
		return self.regs[regnum] if regnum < len(self.regs) else 0
	
	def step(self):
		# Emulate SimRAM_1 component
		ins = self.mem[self.pc:self.pc + 5]
		
		fw = (ins[0] << 48) | (ins[1] << 32) | (ins[2] << 16) | ins[3]
		sw = ins[4]
		
		# Emulate Fetch_1 component
		opcode, func, ra, rb, valC, pcAdd = _fetch(fw, sw)
		valP = self.pc + pcAdd
		
		# Emulate Decode_1 component
		srcA, srcB, dstE, dstM = _decode(opcode, ra, rb)
		
		# Emulate Registers_1 component
		valA = self.getreg(srcA)
		valB = self.getreg(srcB)
		
		# Emulate Execute_1 component
		shouldBranch = self._execute(opcode, valA, valB, valC, func)
		
		# Emulate PCUpdate_1 component
		# TODO: unfinished. This is where I stopped working on this version
		# of the emulator and decided to rewrite it like a normal emulator
		# rather than a hardware-level emulation. See emu.py for the finished
		# and working emulator.


def load_memdump(filename):
	with open(filename, "rb") as fp:
		data8 = fp.read()
	
	# Convert from array of bytes to array of 16-bit words
	data16 = []
	for i in range(0, len(data8), 2):
		# Big-endian
		val = (data8[i] << 8) | data8[i + 1]
		data16.append(val)
	
	return data16


def main():
	cpu = CPU()
	prog = load_memdump("flag-checker-v5.bin")
	cpu.copyin(prog)
	
	flag = [0] * 50
	cpu.copyin(flag, 0xf1a9)
	
	