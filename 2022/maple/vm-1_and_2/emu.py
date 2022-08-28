#!/usr/bin/env python3
import sys
import time

INSTRUCTIONS = (
	"add",
	"sub",
	"xor",
	"and",
	"or",
	"shl",
	"shr",
	"pop",
	"jmp",
	"call",
	"ret",
	"jzr",
	"push",
	"ldm",
	"stm",
	"halt",
)

ALU_INSNS = {
	"add": lambda a, b: (a + b) & 0xff,
	"sub": lambda a, b: (a - b) & 0xff,
	"xor": lambda a, b: a ^ b,
	"and": lambda a, b: a & b,
	"or":  lambda a, b: a | b,
	"shl": lambda a, b: (a << b) & 0xff,
	"shr": lambda a, b: a >> b
}

USES_IMM8 = set([
	"jmp",
	"call",
	"jzr",
	"push"
])


def decode(hexinsn):
	insn = int(hexinsn, 16)
	opcode = (insn >> 8) & 0xf
	imm8 = insn & 0xff
	
	mnemonic = INSTRUCTIONS[opcode]
	return (mnemonic, imm8)


def xxdascii(data):
	s = []
	for c in data:
		if 0x20 <= c <= 0x7e:
			s.append(chr(c))
		else:
			s.append('.')
	return "".join(s)

def disassemble_one(pc, insn):
	mnemonic, imm8 = insn
	if mnemonic in USES_IMM8:
		print("%02X: %s 0x%02x" % (pc, mnemonic, imm8))
	else:
		print("%02X: %s" % (pc, mnemonic))

def disassemble(prog):
	for pc, insn in enumerate(prog):
		disassemble_one(pc, insn)


class Stack:
	def __init__(self, size):
		self.data = [0] * size
		self.sp = 0
	
	def _addsp(self, amount):
		sp = self.sp
		sp += amount
		sp %= len(self.data)
		sp += len(self.data)
		sp %= len(self.data)
		return sp
	
	def push(self, value):
		self.sp = self._addsp(1)
		self.data[self.sp] = value
	
	def pop(self):
		value = self.data[self.sp]
		self.sp = self._addsp(-1)
		return value
	
	def peek(self):
		return self.data[self.sp]
	
	def show(self):
		print("(%s)" % ", ".join(map(hex, self.data[:self.sp + 1])))


class Halted(Exception):
	pass

class MapleCpu:
	def __init__(self, mem_size):
		self.prog = [("halt", 0)]
		self.mem = [0] * mem_size
		self.reset()
		self.quiet = False
	
	def reset(self):
		self.datastack = Stack(10)
		self.callstack = Stack(10)
		self.pc = 0
		self.zf = False
		
		# Debuger stuff
		self.inscount = 0
		self.breakpoints = set([])
		self.watchmem = False
		self.should_log = False
	
	def copyin(self, mem):
		self.mem[:] = mem[:len(self.mem)]
	
	def set_program(self, prog):
		self.prog = prog[:]
	
	def step(self):
		nextpc = self.pc + 1
		insn, imm8 = self.prog[self.pc]
		
		if insn in ALU_INSNS:
			fn = ALU_INSNS[insn]
			a = self.datastack.pop()
			b = self.datastack.pop()
			value = fn(a, b)
			self.datastack.push(value)
			self.zf = (value == 0)
			
			self.log("%s 0x%02x 0x%02x => 0x%02x" % (insn, a, b, value))
		elif insn == "pop":
			self.datastack.pop()
			self.log("pop")
		elif insn == "jmp":
			nextpc = imm8
			self.log("jmp %02X" % nextpc)
		elif insn == "call":
			self.callstack.push(nextpc)
			nextpc = imm8
			self.log("call %02X" % nextpc)
		elif insn == "ret":
			nextpc = self.callstack.pop()
			self.log("ret -> %02x" % nextpc)
		elif insn == "jzr":
			if self.zf:
				nextpc = imm8
				self.log("jzr -> %02X" % nextpc)
			else:
				self.log("jzr (not taken)")
		elif insn == "push":
			self.datastack.push(imm8)
			self.log("push 0x%02x" % imm8)
		elif insn == "ldm":
			addr = self.datastack.pop()
			value = self.mem[addr]
			self.datastack.push(value)
			self.log("ldm [%02X] => 0x%02x" % (addr, value))
		elif insn == "stm":
			value = self.datastack.pop()
			addr = self.datastack.pop()
			self.mem[addr] = value
			if self.watchmem:
				self.showmem()
				time.sleep(0.05)
			self.log("stm [%02X], 0x%02x" % (addr, value))
		elif insn == "halt":
			self.log("halt")
			raise Halted()
		else:
			raise ValueError("Illegal instruction: %s" % insn)
		
		self.inscount += 1
		self.pc = nextpc
	
	def run(self):
		try:
			while True:
				self.step()
				if self.pc in self.breakpoints:
					print("Hit breakpoint at %02X" % self.pc)
					return
		except Halted:
			if not self.quiet:
				print("Program halted")
		except ValueError as e:
			print(e)
	
	def context(self):
		print("PC: %02X" % self.pc)
		print("Call stack:")
		self.callstack.show()
		print("\nData stack:")
		self.datastack.show()
		print("\nNext instructions:")
		for i in range(self.pc, min(self.pc + 5, len(self.prog))):
			disassemble_one(i, self.prog[i])
	
	def showmem(self):
		print("Memory dump:")
		for i in range(0, len(self.mem), 16):
			print(
				"%02X: %02x %02x %02x %02x %02x %02x %02x %02x  %02x %02x %02x %02x %02x %02x %02x %02x  %s" % (
					i, *self.mem[i:i+16], xxdascii(self.mem[i:i+16])
				)
			)
		print("")
	
	def log(self, s):
		if not self.should_log:
			return
		
		print("%02X: %s" % (self.pc, s))
	
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
			elif cmd in ("mem", "xxd", "hexdump"):
				self.showmem()
			elif cmd in ("q", "quit", "exit"):
				break
			elif cmd == "watchmem":
				self.watchmem = not self.watchmem
			elif cmd == "log":
				self.should_log = not self.should_log
			elif cmd in ("h", "help", "?"):
				print("Commands: step, continue, break, context, mem, watchmem")
			else:
				print("Unknown command '%s'" % cmd)


def load_program(filename):
	prog = []
	with open(filename) as fp:
		data = fp.read()
	
	for hexinsn in data.split(" "):
		if len(hexinsn) == 3:
			prog.append(decode(hexinsn))
	
	return prog

def load_data(filename):
	data = []
	with open(filename) as fp:
		for line in fp:
			data.append(int(line, 16))
	
	return data


def main():
	prog = load_program("prog.txt")
	data = load_data("data2.txt")
	
	cpu = MapleCpu(256)
	cpu.quiet = True
	cpu.set_program(prog)
	cpu.copyin(data)
	
	if "--solve" in sys.argv[1:]:
		cpu.run()
		best_inscount = cpu.inscount
		
		# 0x8c is the start of the flag
		brute_pos = 0x8c
		flag = ""
		improved = True
		
		while improved:
			improved = False
			for c in range(0x20, 0x7f):
				data[brute_pos] = c
				cpu.reset()
				cpu.copyin(data)
				cpu.run()
				
				print("Trying '%s': %d" % (flag + chr(c), cpu.inscount))
				
				if cpu.inscount > best_inscount:
					flag += chr(c)
					brute_pos += 1
					best_inscount = cpu.inscount
					improved = True
					break
		
		cpu.showmem()
	else:
		cpu.debugger()


if __name__ == "__main__":
	main()
