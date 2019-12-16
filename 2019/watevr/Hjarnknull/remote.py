from pwn import *

context.log_level = "debug"

r = remote("13.48.59.61", 50000)
r.recvuntil("End program with slut\n")

with open("solution.txt") as code_fp:
	for line in code_fp:
		r.sendline(line.strip())

r.interactive()
