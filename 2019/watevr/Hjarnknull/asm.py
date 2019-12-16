REAL_NAMES = True
scratch_next = 200
scratch_names = []

functions = []

def scratch(name):
	global scratch_next
	result = scratch_next
	scratch_next += 1
	scratch_names.append((result, name))
	return result

symbol_counter = 0
def symbol(name, public=False):
	if public:
		return name
	
	global symbol_counter
	result = "%s_%d" % (name, symbol_counter)
	symbol_counter += 1
	return result

def label(sym):
	return ["label %s" % (sym,)]

if REAL_NAMES:
	def orr(a, b):
		return ["eller %d %d" % (a, b)]

	def inv(a):
		return ["inte %d" % (a,)]

	def jeq(a, b, c):
		return ["testa %d %d @%s" % (a, b, c)]

	def ret():
		return ["poppa"]

	def rdn(a):
		return ["in %d" % (a,)]

	def wrn(a):
		return ["ut %d" % (a,)]

	def lsr(a, b):
		return ["hsh %d %d" % (a, b)]

	def lsl(a, b):
		return ["vsh %d %d" % (a, b)]
else:
	def orr(a, b):
		return ["orr %d %d" % (a, b)]

	def inv(a):
		return ["inv %d" % (a,)]

	def jeq(a, b, c):
		return ["jeq %d %d @%s" % (a, b, c)]

	def ret():
		return ["ret"]

	def rdn(a):
		return ["rdn %d" % (a,)]

	def wrn(a):
		return ["wrn %d" % (a,)]

	def lsr(a, b):
		return ["lsr %d %d" % (a, b)]

	def lsl(a, b):
		return ["lsl %d %d" % (a, b)]


def init():
	return (
		# Get numbers -1 through 10
		lsr(-1, 1)   +
		inv(-1)      +    # $-1 = ~(1 >> 1) = -1
		lsr(0, 1)    +    # $0 = 1 >> 1 = 0
		lsl(2, 1)    +    # $2 = 1 << 1 = 2
		orr(3, 2)    +
		lsl(4, 2)    +    # $4 = 1 << 2 = 4
		orr(5, 4)    +
		lsl(6, 1)    +
		orr(6, 4)    +
		orr(7, 3)    +
		orr(7, 4)    +
		lsl(8, 2)    +    # $8 = 1 << 2 = 4
		lsl(8, 1)    +    # $8 = 4 << 1 = 8
		orr(9, 8)    +
		lsl(10, 1)   +
		orr(10, 8)   +
		
		# Get powers of 2 up to 64
		lsl(16, 4)   +    # $16 = 1 << 4 = 16
		lsl(32, 4)   +
		lsl(32, 1)   +    # $32 = (1 << 4) << 1 = 32
		lsl(64, 4)   +
		lsl(64, 2)   +    # $64 = (1 << 4) << 2 = 64
		
		# Get 2**n - 1 (for masks) up to 63
		orr(15, 7)   +
		orr(15, 8)   +
		orr(31, 15)  +
		orr(31, 16)  +
		orr(63, 31)  +
		orr(63, 32)  +
		
		# Get 65 (useful for shifting to check sign bit)
		orr(65, 64)  +
		
		# Get 1 << 65
		lsl(165, 65)      # $165 = 1 << 65
	)

def zero(x):
	""" x = 0 == ~(x | -1) """
	return (
		orr(x, -1) +
		inv(x)
	)

def mov(x, y):
	""" x = y == zero(x); x |= y """
	return (
		zero(x) +
		orr(x, y)
	)

def bit_and(x, y):
	""" x & y == ~(~x | ~y)"""
	tmp = scratch("bit_and.tmp")
	
	return (
		inv(x) +
		mov(tmp, y) +
		inv(tmp) +
		orr(x, tmp) +
		inv(x)
	)

def call(target):
	""" if 0 == 0 call target """
	return jeq(0, 0, target)

def add_bad(x, y_arg):
	add_return_y = symbol("add.return_y")
	add_check_y_zero = symbol("add.check_y_zero")
	add_loop_cond = symbol("add.loop_cond")
	add_x_carryin_false = symbol("add.x_carryin_false")
	add_x_y_carryin_false = symbol("add.x_y_carryin_false")
	add_x_bit_zero = symbol("add.x_bit_zero")
	add_not_x_carryin_false = symbol("add.not_x_carryin_false")
	add_not_x_y_carryin_false = symbol("add.not_x_y_carryin_false")
	add_after_addone = symbol("add.after_addone")
	add_after_loop = symbol("add.after_loop")
	add_carryout_false = symbol("add.carryout_false")
	add_x_not_sign = symbol("add.x_not_sign")
	add_y_not_sign = symbol("add.y_not_sign")
	add_return_x = symbol("add.return_x")
	
	y = scratch("add.y")
	bit = scratch("add.bit")
	mask = scratch("add.mask")
	carryIn = scratch("add.carryIn")
	carryOut = scratch("add.carryOut")
	notbit = scratch("add.notbit")
	tmp = scratch("add.tmp")
	sign = scratch("add.sign")
	
	return (
		mov(y, y_arg) +
		
		mov(bit, 1) +
		zero(mask) +
		
		jeq(x, 0, add_return_y) +
		call(add_check_y_zero) +
		
	label(add_return_y) +
		mov(x, y) +
		call(add_return_x) +
		
	label(add_check_y_zero) +
		jeq(y, 0, add_return_x) +
		
		zero(carryOut) +
		
	label(add_loop_cond) +
		jeq(bit, 165, add_after_loop) +
		# while bit != 1 << 65:
			mov(carryIn, carryOut) +
			zero(carryOut) +
			
			mov(notbit, bit) +
			inv(notbit) +
			
			mov(tmp, x) +
			bit_and(tmp, bit) +
			
			# if x & bit:
			jeq(tmp, 0, add_x_bit_zero) +
				# if carryIn:
				jeq(carryIn, 0, add_x_carryin_false) +
					bit_and(x, notbit) +
					mov(carryOut, 1) +
				
				# else:
				label(add_x_carryin_false) +
					mov(tmp, y) +
					bit_and(tmp, bit) +
					
					# if y & bit:
					jeq(tmp, 0, add_after_addone) +
						# if carryIn:
						jeq(carryIn, 0, add_x_y_carryin_false) +
							orr(x, bit) +
							call(add_after_addone) +
						# else:
						label(add_x_y_carryin_false) +
							bit_and(x, notbit) +
							mov(carryOut, 1) +
							call(add_after_addone) +
			# else:
			label(add_x_bit_zero) +
				# if carryIn:
				jeq(carryIn, 0, add_not_x_carryin_false) +
					orr(x, bit) +
			label(add_not_x_carryin_false) +
				mov(tmp, y) +
				bit_and(tmp, bit) +
				jeq(tmp, 0, add_after_addone) +
				
				#if carryIn:
				jeq(carryIn, 0, add_not_x_y_carryin_false) +
					bit_and(x, notbit) +
					mov(carryOut, 1) +
					call(add_after_addone) +
				#else:
				label(add_not_x_y_carryin_false) +
					orr(x, bit) +
			
		label(add_after_addone) +
			lsl(bit, 1) +
			lsl(mask, 1) +
			orr(mask, 1) +
			call(add_loop_cond) +
		
	label(add_after_loop) +
		zero(sign) +
		
		# if not carryOut:
		jeq(carryOut, 0, add_carryout_false) +
			inv(sign) +
		
	label(add_carryout_false) +
		mov(tmp, x) +
		bit_and(tmp, 165) +
		
		# if x & (1 << 65):
		jeq(tmp, 0, add_x_not_sign) +
			inv(sign) +
		
	label(add_x_not_sign) +
		mov(tmp, y) +
		bit_and(tmp, 165) +
		
		# if y & (1 << 65):
		jeq(tmp, 0, add_y_not_sign) +
			inv(sign) +
		
	label(add_y_not_sign) +
		bit_and(x, mask) +
		inv(mask) +
		bit_and(sign, mask) +
		orr(x, sign) +
	
	label(add_return_x)
	)

def gate_not(a, result):
	return (
		mov(result, a) +
		inv(result)
	)

def gate_or(a, b, result):
	return (
		mov(result, a) +
		orr(result, b)
	)

def gate_and(a, b, result):
	"""
	Returns -1 in result if both a and b are nonzero, 0 otherwise.
	"""
	bool_and_false = symbol("gate_and.false")
	bool_and_return = symbol("gate_and.return")
	
	return (
		jeq(a, 0, bool_and_false) +
		jeq(b, 0, bool_and_false) +
		orr(result, -1) +
		jeq(0, 0, bool_and_return) +
	label(bool_and_false) +
		zero(result) +
	label(bool_and_return)
	)

def gate_nand(a, b, result):
	return (
		gate_and(a, b, result) +
		inv(result)
	)

def gate_xor(a, b, result):
	"""
	Given boolean values a and b, where 0 is false and -1 is true, set result to a ^ b.
	"""
	bool_xor_false = symbol("gate_xor.false")
	bool_xor_return = symbol("gate_xor.return")
	
	return (
		jeq(a, b, bool_xor_false) +
		orr(result, -1) +
		jeq(0, 0, bool_xor_return) +
	label(bool_xor_false) +
		zero(result) +
	label(bool_xor_return)
	)

def half_adder(a, b, s, cout):
	return (
		gate_xor(a, b, s) +
		gate_and(a, b, cout)
	)

def full_adder(p, q, cin, cout, s):
	tmp_s = scratch("full_adder.tmp_s")
	tmp_co1 = scratch("full_adder.tmp_co1")
	tmp_co2 = scratch("full_adder.tmp_co2")
	
	return (
		half_adder(p, q, tmp_s, tmp_co1) +
		half_adder(cin, tmp_s, s, tmp_co2) +
		gate_or(tmp_co1, tmp_co2, cout)
	)

def num_to_bits(n, start):
	bit = scratch("num_to_bits.bit")
	tmp = scratch("num_to_bits.tmp")
	
	insns = []
	for i in range(64):
		insns.extend(orr(start + i, -1))
	
	insns.extend(mov(bit, 1))
	
	for i in range(64):
		bit_is_set = symbol("decode_bit_%d_is_set" % i)
		insns.extend(
			mov(tmp, n) +
			bit_and(tmp, bit) +
			jeq(tmp, bit, bit_is_set) +
			zero(start + i) +
		label(bit_is_set) +
			lsl(bit, 1)
		)
	
	return insns

def bits_to_num(start, n):
	bit = scratch("bits_to_num.bit")
	
	insns = []
	
	insns.extend(
		zero(n) +
		mov(bit, 1)
	)
	
	for i in range(64):
		bit_is_zero = symbol("encode_bit_%d_is_zero" % i)
		insns.extend(
			jeq(start + i, 0, bit_is_zero) +
			orr(n, bit) +
		label(bit_is_zero)
		)
		
		if i != 63:
			insns.extend(lsl(bit, 1))
	
	return insns

def add_insane(x, y, result):
	x_start = 700
	y_start = 800
	r_start = 900
	
	carryIn = scratch("add.carryIn")
	carryOut = scratch("add.carryOut")
	
	insns = []
	
	insns.extend(
		num_to_bits(x, x_start) +
		num_to_bits(y, y_start) +
		zero(carryIn)
	)
	
	for i in range(64):
		insns.extend(
			full_adder(x_start + i, y_start + i, carryIn, carryOut, r_start + i)
		)
		
		if i != 63:
			insns.extend(mov(carryIn, carryOut))
	
	insns.extend(bits_to_num(r_start, result))
	
	return insns

def xor(x, y):
	xor_loop = symbol("xor.loop")
	xor_next_bit = symbol("xor.next_bit")
	xor_turn_bit_on = symbol("xor.turn_bit_on")
	xor_done = symbol("xor.done")
	
	bit = scratch("xor.bit")
	tmp = scratch("xor.tmp")
	
	return (
		mov(bit, 1) +
		
		# while bit != 1 << 65:
	label(xor_loop) +
		jeq(bit, 165, xor_done) +
			# if y & bit:
			mov(tmp, y) +
			orr(tmp, bit) +
			jeq(tmp, 0, xor_next_bit) +
				# if x & bit:
				mov(tmp, x) +
				orr(tmp, bit) +
				jeq(tmp, 0, xor_turn_bit_on) +
					# At this point, tmp == bit
					
					# x &= ~bit
					inv(tmp) +
					bit_and(x, tmp) +
				# else:
				label(xor_turn_bit_on) +
					# x |= bit
					orr(x, bit) +
			
		label(xor_next_bit) +
			# bit <<= 1
			lsl(bit, 1) +
			call(xor_loop) +
	label(xor_done)
		
		# TODO: handle sign
	)


def add_bit_body(x, y, carryIn, result, carryOut):
	"""
	add_bit(x, y, carryIn, result, carryOut):
		result = 0
		carryOut = 0
		
		if x | 1   == x: call got_bit
		if y | 1   == y: call got_bit
		if carryIn == -1: call got_bit
		
		ret
	
	got_bit:
		carryOut |= result
		result = ~result
		ret
	"""
	
	my_got_bit = symbol("add_bit.got_bit")
	my_set_bit = symbol("add_bit.set_bit")
	
	tmp = scratch("add_bit.tmp")
	
	return (
		zero(result) +
		zero(carryOut) +
		
		mov(tmp, x) +
		orr(tmp, 1) +
		jeq(tmp, x, my_got_bit) +
		
		mov(tmp, y) +
		orr(tmp, 1) +
		jeq(tmp, y, my_got_bit) +
		
		jeq(carryIn, -1, my_got_bit) +
		
		ret() +
		
	label(my_got_bit) +
		orr(carryOut, result) +
		inv(result) +
		ret()
	)


sym_add_bit = symbol("add_bit", public=True)
add_bit_x = scratch("add_bit.x")
add_bit_y = scratch("add_bit.y")
add_bit_carryIn = scratch("add_bit.carryIn")
add_bit_result = scratch("add_bit.result")
add_bit_carryOut = scratch("add_bit.carryOut")
add_bit_emitted = False
def add_bit(x, y, carryIn, result, carryOut):
	global add_bit_emitted
	if not add_bit_emitted:
		add_bit_emitted = True
		
		functions.extend(
		label(sym_add_bit) +
			add_bit_body(add_bit_x, add_bit_y, add_bit_carryIn, add_bit_result, add_bit_carryOut)
		)
	
	return (
		mov(add_bit_x, x) +
		mov(add_bit_y, y) +
		mov(add_bit_carryIn, carryIn) +
		call(sym_add_bit) +
		mov(result, add_bit_result) +
		mov(carryOut, add_bit_carryOut)
	)

def add_body(x, y, result):
	"""
	add(x, y, result):
		result = 0
		bit = 1
		carryOut = 0
		mask = 0
		shouldBreak = 0
		
		call add_loop
		
		# Copy the sign bits from carryOut onto the result
		result |= carryOut & ~mask
		return result
	
	add_loop:
		carryIn = carryOut
		s, carryOut = add_bit(x, y, carryIn)
		if s == -1: call set_bit
		
		bit <<= 1
		mask <<= 1
		mask |= 1
		x >>= 1
		y >>= 1
		
		if x == 0: call x_zero
		if x == -1: call x_negone
		
		if shouldBreak == 0: call add_loop
		ret
	
	set_bit:
		result |= bit
		ret
	
	x_zero:
		if y == 0: call x_zero_y_zero
		if y == -1: call flip_break
		ret
	
	x_zero_y_zero:
		if carryOut == 0: call set_break
		else:
			# There's a carry-out, but both x and y are zero,
			# so the carry-out will be handled in the next
			# loop iteration
			continue
		ret
	
	flip_break:
		# The remaining sign bits of the result will be
		# the opposite of carryOut.
		carryOut = ~carryOut
		shouldBreak = -1
		ret
	
	set_break:
		shouldBreak = -1
		ret
	
	x_negone:
		if y == 0: call flip_break
		if y == -1: call set_break
			# The sign bits of x and y are identical,
			# meaning they will cancel each other out during
			# the addition. That means that the sign bits of
			# the result will be set to carryOut
		ret
	"""
	
	add_loop = symbol("add.loop")
	set_bit = symbol("add.set_bit")
	x_zero = symbol("add.x_zero")
	x_zero_y_zero = symbol("add.x_zero_y_zero")
	flip_break = symbol("add.flip_break")
	set_break = symbol("add.set_break")
	x_negone = symbol("add.x_negone")
	
	bit = scratch("add.bit")
	carryOut = scratch("add.carryOut")
	carryIn = scratch("add.carryIn")
	mask = scratch("add.mask")
	shouldBreak = scratch("add.shouldBreak")
	tmp = scratch("add.tmp")
	
	return (
		zero(result) +
		mov(bit, 1) +
		zero(carryOut) +
		zero(mask) +
		zero(shouldBreak) +
		
		call(add_loop) +
		
		# result |= carryOut & ~mask
		mov(tmp, mask) +
		inv(tmp) +
		bit_and(tmp, carryOut) +
		orr(result, tmp) +
		ret() +
		
	label(add_loop) +
		mov(carryIn, carryOut) +
		add_bit(x, y, carryIn, tmp, carryOut) +
		jeq(tmp, -1, set_bit) +
		
		lsl(bit, 1) +
		lsl(mask, 1) +
		orr(mask, 1) +
		lsr(x, 1) +
		lsr(y, 1) +
		
		jeq(x, 0, x_zero) +
		jeq(x, -1, x_negone) +
		
		jeq(shouldBreak, 0, add_loop) +
		ret() +
		
	label(set_bit) +
		orr(result, bit) +
		ret() +
		
	label(x_zero) +
		jeq(y, 0, x_zero_y_zero) +
		jeq(y, -1, flip_break) +
		ret() +
		
	label(x_zero_y_zero) +
		jeq(carryOut, 0, set_break) +
		ret() +
		
	label(flip_break) +
		inv(carryOut) +
		orr(shouldBreak, -1) +
		ret() +
		
	label(set_break) +
		orr(shouldBreak, -1) +
		ret() +
		
	label(x_negone) +
		jeq(y, 0, flip_break) +
		jeq(y, -1, set_break) +
		ret()
	)

sym_add = symbol("add", public=True)
add_x = scratch("add.x")
add_y = scratch("add.y")
add_result = scratch("add.result")
add_emitted = False
def add(x, y, result):
	global add_emitted
	if not add_emitted:
		add_emitted = True
		functions.extend(
		label(sym_add) +
			add_body(add_x, add_y, add_result)
		)
	
	return (
		mov(add_x, x) +
		mov(add_y, y) +
		call(sym_add) +
		mov(result, add_result)
	)

def addi(x, y):
	return add(x, y, x)

def neg(x, result):
	tmp = scratch("neg.tmp")
	
	return (
		mov(tmp, x) +
		inv(tmp) +
		add(tmp, 1, result)
	)

def negi(x):
	return neg(x, x)

def sub(x, y, result):
	tmp = scratch("sub.tmp")
	
	return (
		neg(y, tmp) +
		add(x, tmp, result)
	)

def subi(x, y):
	return sub(x, y, x)

def mul_body(x, y, result):
	"""
	mul_body(x, y, result):
		result = 0
		sign = 0
		shouldBreak = 0
		
		if x >> 64 == -1: call x_neg
		if y >> 64 == -1: call y_neg
		
		if y == 0: call set_break
		if shouldBreak == 0: call mul_loop
		
		if sign == -1: call r_neg
		ret
	
	x_neg:
		negi(x)
		sign = ~sign
		ret
	
	y_neg:
		negi(y)
		sign = ~sign
		ret
	
	r_neg:
		negi(result)
		ret
	
	set_break:
		shouldBreak = -1
		ret
	
	mul_loop:
		if y | 1 == y: call add_x
		
		x <<= 1
		y >>= 1
		
		if y == 0: call set_break
		if shouldBreak == 0: call mul_loop
		ret
	
	add_x:
		addi(result, x)
		ret
	"""
	
	x_neg = label("mul_body.x_neg")
	y_neg = label("mul_body.y_neg")
	r_neg = label("mul_body.r_neg")
	set_break = label("mul_body.set_break")
	mul_loop = label("mul_body.mul_loop")
	add_x = label("mul_body.add_x")
	
	sign = scratch("mul_body.sign")
	shouldBreak = scratch("mul_body.shouldBreak")
	tmp = scratch("mul_body.tmp")
	
	return (
		zero(result) +
		zero(sign) +
		zero(shouldBreak) +
		
		mov(tmp, x) +
		lsr(tmp, 64) +
		jeq(tmp, -1, x_neg) +
		
		mov(tmp, y) +
		lsr(tmp, 64) +
		jeq(tmp, -1, y_neg) +
		
		jeq(y, 0, set_break) +
		jeq(shouldBreak, 0, mul_loop) +
		
		jeq(sign, -1, r_neg) +
		ret() +
		
	label(x_neg) +
		negi(x) +
		inv(sign) +
		ret() +
		
	label(y_neg) +
		negi(y) +
		inv(sign) +
		ret() +
		
	label(r_neg) +
		negi(result) +
		ret() +
		
	label(set_break) +
		orr(shouldBreak, -1) +
		ret() +
		
	label(mul_loop) +
		mov(tmp, y) +
		orr(tmp, 1) +
		jeq(tmp, y, add_x) +
		
		lsl(x, 1) +
		lsr(y, 1) +
		
		jeq(y, 0, set_break) +
		jeq(shouldBreak, 0, mul_loop) +
		ret() +
		
	label(add_x) +
		addi(result, x) +
		ret()
	)

sym_mul = symbol("mul", public=True)
mul_x = scratch("mul.x")
mul_y = scratch("mul.y")
mul_result = scratch("mul.result")
mul_emitted = False
def mul(x, y, result):
	global mul_emitted
	if not mul_emitted:
		mul_emitted = True
		functions.extend(
		label(sym_mul) +
			mul_body(mul_x, mul_y, mul_result)
		)
	
	return (
		mov(mul_x, x) +
		mov(mul_y, y) +
		call(sym_mul) +
		mov(result, mul_result)
	)

def hjarn_main():
	hjarn_input = symbol("hjarn.input")
	hjarn_add = symbol("hjarn.add")
	hjarn_sub = symbol("hjarn.sub")
	hjarn_mul = symbol("hjarn.mul")
	hjarn_result = symbol("hjarn.result")
	
	action = scratch("hjarn.action")
	x = scratch("hjarn.x")
	y = scratch("hjarn.y")
	r = scratch("hjarn.r")
	
	return (
		init() +
		call(hjarn_input) +
		ret() +
		
	label(hjarn_input) +
		rdn(action) +
		rdn(x) +
		rdn(y) +
		
		# switch(action) {
		jeq(action, 0, hjarn_add) +
		jeq(action, 1, hjarn_sub) +
		jeq(action, 2, hjarn_mul) +
		wrn(r) +
		call(hjarn_input) +
		ret() +
		
		# case ADD:
	label(hjarn_add) +
		add(x, y, r) +
		ret() +
		
		# case SUB:
	label(hjarn_sub) +
		sub(x, y, r) +
		ret() +
		
		#case MUL:
	label(hjarn_mul) +
		mul(x, y, r) +
		ret()
	)

def resolve_labels(asm, showAddrs=False):
	labels = {}
	insns = []
	
	ip = 0
	for item in asm:
		if item.startswith("label "):
			labels[item[len("label "):]] = ip
		else:
			ip += 1
	
	ip = 0
	for item in asm:
		if not item.startswith("label "):
			if showAddrs:
				prefix = "%d: " % ip
			else:
				prefix = ""
			
			if "@" in item:
				mnemonic, label = item.split("@")
				insns.append(prefix + mnemonic + str(labels[label]))
			else:
				insns.append(prefix + item)
			
			ip += 1
	
	return insns

def simple_test():
	loop_top = symbol("loop_top")
	loop_end = symbol("loop_end")
	
	count = scratch("count")
	i = scratch("i")
	
	return (
		init() +
		
		# count = input()
		rdn(count) +
		
		# for(i = 1; i != count; i <<= 1) {
	label(loop_top) +
		jeq(i, count, loop_end) +
			# print(i)
			wrn(i) +
			
			lsl(i, 1) +
			call(loop_top) +
		
		# }
	label(loop_end)
	)

def test_xor():
	test_xor_loop = symbol("test_xor.loop")
	
	x = scratch("test_xor.x")
	y = scratch("test_xor.y")
	
	return (
		init() +
		
	label(test_xor_loop) +
		rdn(x) +
		rdn(y) +
		xor(x, y) +
		wrn(x) +
		call(test_xor_loop)
	)

def main():
	asm_with_labels = hjarn_main() + functions
	asm = resolve_labels(asm_with_labels, showAddrs=False)
	for insn in asm:
		print(insn)
	print("slut")
	
	with open("scratch.map", "w") as scratch_fp:
		for value, name in scratch_names:
			scratch_fp.write("%d=%s\n" % (value, name))


if __name__ == "__main__":
	main()
