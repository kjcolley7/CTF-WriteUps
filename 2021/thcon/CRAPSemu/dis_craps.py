#!/usr/bin/env python
import struct
import sys

program = [
	0xba002200, 0x1000020, 0x8290603a, 0xba276001,
	0xc2274000, 0x164726f, 0x82906077, 0xba276001,
	0xc2274000, 0x1737361, 0x82906050, 0xba276001,
	0xc2274000, 0x82002001, 0x84904000, 0x86974000,
	0x8800200a, 0x40000000, 0x82184001, 0x84904000,
	0x86002100, 0x88002018, 0x40000000, 0xba002200,
	0x1321695, 0x8290603e, 0xba276001, 0xc2274000,
	0x12740af, 0x82906039, 0xba276001, 0xc2274000,
	0x17768c5, 0x8290603c, 0xba276001, 0xc2274000,
	0x14c6ac1, 0x82906020, 0xba276001, 0xc2274000,
	0x1290dab, 0x8290604e, 0xba276001, 0xc2274000,
	0x14176a0, 0x8290605e, 0xba276001, 0xc2274000,
	0x80180005, 0x61337f0, 0x8c91a00d, 0x80a76200,
	0x2200000a, 0xc8074000, 0xba076001, 0x88190006,
	0xc400c000, 0x8600e001, 0x80a10002, 0x23fffff8,
	0x8a116001, 0x31fffff6, 0x80a14000, 0x22000019,
	0xba976200, 0x10a2e64, 0x82906072, 0xba276001,
	0xc2274000, 0x16f7773, 0x82906073, 0xba276001,
	0xc2274000, 0x1617020, 0x82906067, 0xba276001,
	0xc2274000, 0x16e6f72, 0x82906057, 0xba276001,
	0xc2274000, 0x82002001, 0x84904000, 0x86974000,
	0x88002010, 0x40000000, 0x84002001, 0x3000001b,
	0xba976200, 0x8200200a, 0xba276001, 0xc2274000,
	0x121736e, 0x8290606f, 0xba276001, 0xc2274000,
	0x1697461, 0x8290606c, 0xba276001, 0xc2274000,
	0x1757461, 0x82906072, 0xba276001, 0xc2274000,
	0x1676e6f, 0x82906043, 0xba276001, 0xc2274000,
	0x82002001, 0x84904000, 0x86974000, 0x88002011,
	0x40000000, 0x84188002, 0x82002002, 0x40000000
]

if len(sys.argv) >= 2:
	with open(sys.argv[1], "r") as f:
		rom = f.read().ljust(4, "\0")
	program = [struct.unpack("<I", rom[i:i+4])[0] for i in range(0, len(rom), 4)]
	SYMBOLS, COMMENTS = {}, {}
else:
	SYMBOLS = {
		0x33: 'validate_password',
		0x3c: 'invalid_password',
		0x3e: 'check_if_matched',
		0x40: 'print_wrong_password',
		0x58: 'print_congratulations',
		0x72: 'exit'
	}
	
	COMMENTS = {
		0x11: 'printf("Password: ")',
		0x16: 'read(STDIN_FILENO, 0x100, 0x18)',
		0x17: 'Start building password in memory',
		0x31: 'Value XORed against each DWORD in the password',
	}

def x13(val):
	sign = -((val >> 12) & 1)
	sign &= 0xfffffe00
	return sign | (val & 0x1fff)

def x25(val):
	sign = -((val >> 24) & 1)
	sign &= 0xfe000000
	return sign | (val & 0x1ffffff)

def dis_multiple(insns, start_addr):
	lines = []
	bb_starts = set()
	for i, insn in enumerate(insns):
		addr = start_addr + i
		asm, bb = dis_insn(insn, addr)
		
		if bb is not None:
			bb_starts.add(bb)
			bb_starts.add(addr + 1)
		
		sym = SYMBOLS.get(addr, "")
		if sym:
			sym = "\n%s:\n" % (sym,)
		
		line = "%s0x%04x: %s" % (sym, addr, asm)
		if addr in COMMENTS:
			line = "%-40s# %s" % (line, COMMENTS[addr])
		
		lines.append(line)
	
	bbs = []
	cur_bb = []
	
	for i, line in enumerate(lines):
		addr = start_addr + i
		if addr in bb_starts:
			bbs.append(cur_bb)
			cur_bb = []
		cur_bb.append(line)
	bbs.append(cur_bb)
	
	return bbs

def dis_insn(insn, addr):
	if (insn >> 31) & 1:
		return dis_xyz(insn), None
	
	if (insn >> 30) & 1:
		return "syscall", None
	
	if (insn >> 29) & 1:
		return dis_jcc(insn, addr)
	
	return dis_movt(insn), None

def dis_xyz(insn):
	# Decoding
	rz = (insn >> 25) & 0x1f
	opcode = (insn >> 19) & 0x3f
	rx = (insn >> 14) & 0x1f
	
	if (insn >> 13) & 1:
		is_imm = True
		imm13 = x13(insn)
	else:
		is_imm = False
		ry = insn & 0x1f
	
	is_mem = bool((insn >> 30) & 1)
	
	# Formatting
	mnemonic = get_mnemonic(opcode)
	
	rxn = get_reg_name(rx)
	rzn = get_reg_name(rz)
	if is_imm:
		ryn = hex(imm13)
		if 0x20 <= imm13 <= 0x7e:
			ryn += " ('%s')" % (chr(imm13),)
	else:
		ryn = get_reg_name(ry)
	
	if is_mem:
		if mnemonic == "add":
			return "ldr     %s, [%s+%s]" % (rzn, rxn, ryn)
		elif mnemonic == "sub":
			return "str     %s, [%s+%s]" % (rzn, rxn, ryn)
		else:
			mnemonic = "ILL2"
	
	
	if opcode >= 0x20:
		args = (rzn, rxn)
	else:
		args = (rzn, rxn, ryn)
	
	if mnemonic == "subs" and rz == 0:
		mnemonic = "cmp"
		args = (rxn, ryn)
	elif mnemonic.startswith("orr") and rz == rx and is_imm:
		mnemonic = "movb"
		args = (rzn, ryn)
	
	fmt = ", ".join(["%s"] * len(args))
	return ("%-8s" + fmt) % ((mnemonic,) + args)

def dis_jcc(insn, addr):
	cond = (insn >> 25) & 0xf
	cond_name = {
		0x0: "ILL3",
		0x1: "eq",
		0x2: "le1",
		0x3: "lt",
		0x4: "le2",
		0x5: "vs",
		0x6: "ng",
		0x7: "cs",
		0x8: "mp",
		0x9: "ne",
		0xA: "gt1",
		0xB: "ge",
		0xC: "gt2",
		0xD: "vc",
		0xE: "ps",
		0xF: "cc",
	}[cond]
	
	target = (addr + x25(insn)) & 0xffffffff
	
	return "j%-7s%s" % (cond_name, format_addr(target)), target

def dis_movt(insn):
	rz = (insn >> 24) & 0x1f
	rzn = get_reg_name(rz)
	
	imm24 = insn & 0xffffff
	
	l = list(struct.pack("<I", imm24))
	s = ""
	for c in l:
		if 0x20 <= ord(c) <= 0x7e:
			s += c
	
	return "movt    %s, %#x ('%s')" % (rzn, imm24, s)

def format_addr(addr, width=None):
	if addr in SYMBOLS:
		s = SYMBOLS[addr]
	else:
		s = "0x%04x" % (addr,)
	
	if width is not None:
		return ("%-" + str(width) + "s") % (s,)
	else:
		return s

def get_reg_name(r):
	regmap = {
		0x00: "ZERO",
		0x15: "TMP",
		0x1E: "PC",
		0x1F: "FETCH",
	}
	
	if r in regmap:
		return regmap[r]
	else:
		return "R%d" % r

def get_mnemonic(op):
	return {
		0x00: "add",
		0x01: "and",
		0x02: "orr",
		0x03: "xor",
		0x04: "sub",
		0x0D: "shr",
		0x0E: "shl",
		0x10: "adds",
		0x11: "ands",
		0x12: "orrs",
		0x13: "xors",
		0x14: "subs",
		0x20: "x13",
		0x21: "x25",
		0x23: "sl8",
	}.get(op, "ILL1")

if __name__ == "__main__":
	for bb in dis_multiple(program, 0):
		for line in bb:
			print(line)
		print("")
