"""

instructions:

orr A, B    = eller
inv A       = inte
jeq A, B, C = testa
ret         = poppa
rdn A       = in
wrn A       = ut
lsr A, B    = hsh
lsl A, B    = vsh

pseudoinstructions:

init():
	lsr 0 1   # $0 = 1 >> 1 = 0
	lsl 2 1   # $2 = 1 << 1 = 2
	lsl 4 2   # $4 = 1 << 2 = 4
	lsl 8 2   # $8 = 1 << 2 = 4
	lsl 8 1   # $8 = 4 << 1 = 8
	lsl 16 4  # $16 = 1 << 4 = 16
	lsl 32 4
	lsl 32 1  # $32 = (1 << 4) << 1 = 32
	lsl 64 4
	lsl 62 2  # $64 = (1 << 4) << 2 = 64
	lsr -1 1
	inv -1    # $-1 = ~(1 >> 1) = -1
	orr 3 2
	orr 7 3
	orr 7 4
	orr 15 7
	orr 15 8
	orr 31 15
	orr 31 16
	orr 63 31
	orr 63 32
	orr 65 64
	lsl 165 65 # $165 = 1 << 65


jmp(target):
	jeq 0, 0, target


zero_pos(x):
	lsr x, 64


zero(x):
	zero_pos(x)
	jeq x, 0, zero_return
	inv x
	zero_pos(x)
zero_return:


mov(x, y):
	zero(x)
	orr(x, y)


and(x, y): # x & y == ~(~x | y)
	inv x
	orr x, y
	inv x


add(x, y_arg):
	mov(y, y_arg)
	
	# bit = 1; mask = 0
	mov(bit, 1)
	zero(mask)
	
	# if x == 0: return y
	jeq x, 0, add_return_y
	jmp add_check_y_zero
	
add_return_y:
	mov(x, y)
	jmp add_return_x
	
	# if y == 0: return x
add_check_y_zero:
	jeq y, 0, add_return_x
	
	# carryOut = False
	zero(carryOut)
	
	# while bit != 1 << 65:
add_loop_cond:
	jeq bit, 165, add_after_loop
	
	# carryIn = carryOut; carryOut = False
	mov(carryIn, carryOut)
	zero(carryOut)
	
	# notbit = ~bit
	mov(notbit, bit)
	inv notbit
	
	# if x & bit:
	mov(tmp, x)
	and(tmp, bit)
	jeq tmp, 0, add_x_bit_zero
	
	# if carryIn:
	jeq carryIn, 0, add_x_carryIn_false
	
	# x &= ~bit; carryOut = True
	and(x, notbit)
	mov(carryOut, 1)
	
add_x_carryIn_false:
	# if y & bit:
	mov(tmp, y)
	and(tmp, bit)
	jeq tmp, 0, add_x_y_bit_zero
	
	# if carryIn:
	jeq carryIn, 0, add_xy_carryIn_false
	
	# x |= bit
	orr x, bit
	jmp add_after_addone
	
	# else: (attached to if carryIn)
add_xy_carryIn_false:
	# x &= ~bit; carryOut = True
	and(x, notbit)
	mov(carryOut, 1)
	jmp add_after_addone
	
	# else: (attached to if x & bit)
add_x_bit_zero:
	# if carryIn:
	jeq carryIn, 0, add_not_x_carryIn_false
	
	# x |= bit
	orr x, bit
	
add_not_x_carryIn_false:
	# if y & bit:
	mov(tmp, y)
	and(tmp, bit)
	jeq tmp, 0, add_after_addone
	
	# if carryIn:
	jeq carryIn, 0, add_not_x_y_carryIn_false
	
	# x &= bit; carryOut = True
	and(x, notbit)
	mov(carryOut, 1)
	jmp add_after_addone
	
	# else: (attached to if carryIn)
add_not_x_y_carryIn_false:
	# x |= bit
	orr x, bit
	
add_after_addone:
	# bit <<= 1; mask <<= 1; mask |= 1
	lsl bit, 1
	lsl mask, 1
	orr mask, 1
	jmp add_loop_cond
	
add_after_loop:
	zero(sign)
	jeq carryOut, 0, add_carryout_false
	inv sign
	
add_carryout_false:
	mov(tmp, x)
	and(tmp, 165)
	jeq tmp, 0, add_x_not_sign
	inv sign
	
add_x_not_sign:
	mov(tmp, y)
	and(tmp, 165)
	jeq tmp, 0, add_y_not_sign
	inv sign
	
add_y_not_sign:
	and(x, mask)
	inv mask
	and(sign, mask)
	orr x, sign
	
add_return_x:


neg(x): # -x = ~x + 1
	inv x
	add(x, 1)


sub(x, y): # x - y = x + (-y)
	mov(tmp, y)
	neg(tmp)
	add(x, tmp)


mul(x, y_arg):
	mov(y, y_arg)
	mov(result, 0)
	mov(sign, 0)
	
	jeq x, 0, mul_return #if(x == 0 || y == 0) return;
	jeq y, 0, mul_return
	
	mov(tmp, x)
	lsr tmp, 64
	jeq tmp, 0, mul_x_is_positive
	inv sign
	neg(x)
	
mul_x_is_positive:
	mov(tmp, y)
	lsr tmp, 64
	jeq tmp, 0, mul_loop
	inv sign
	neg(y)
	
mul_loop:
	add(result, x)
	sub(y, 1)
	jeq y, 0, mul_sign_return
	jmp mul_loop
	
mul_sign_return:
	jeq sign, 0, mul_return
	neg(result)
	
mul_return:
	mov(x, result)


hjarn_main():
	init()
	
hjarn_input:
	rdn action
	rdn x
	rdn y
	jeq(action, 0, hjarn_add)
	jeq(action, 1, hjarn_sub)
	jeq(action, 2, hjarn_mul)
	
hjarn_add:
	add(x, y)
	jmp(hjarn_result)
	
hjarn_sub:
	sub(x, y)
	jmp(hjarn_result)
	
hjarn_mul:
	mul(x, y)
	jmp(hjarn_result)
	
hjarn_result:
	wrn x
	jmp(hjarn_input)
"""
