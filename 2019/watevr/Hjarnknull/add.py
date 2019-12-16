def add_old(x, y, verbose=False):
	bit = 1
	mask = 0
	
	if x == 0:
		return y
	if y == 0:
		return x
	
	if verbose:
		print("x: %s (%d)" % (bin(x), x))
		print("y: %s (%d)" % (bin(y), y))
		print("x + y: %s (%d)" % (bin(x + y), x + y))
	
	carryOut = False
	while bit != 1 << 65:
		carryIn = carryOut
		carryOut = False
		notbit = ~bit
		
		if verbose:
			print("x: %s (%d)" % (bin(x), x))
			print("y: %s (%d)" % (bin(y), y))
			print("carryIn: %d" % carryIn)
			print("bit: %s" % bin(bit))
		
		if x & bit:
			if carryIn:
				x &= notbit
				carryOut = True
			if y & bit:
				if carryIn:
					x |= bit
				else:
					x &= notbit
					carryOut = True
		else:
			if carryIn:
				x |= bit
			if y & bit:
				if carryIn:
					x &= notbit
					carryOut = True
				else:
					x |= bit
		
		if verbose:
			print("carryOut: %d" % carryOut)
			print("============")
		
		bit <<= 1
		mask <<= 1
		mask |= 1
	
	sign = 0
	if carryOut:
		sign = ~sign
	if x & bit:
		sign = ~sign
	if y & bit:
		sign = ~sign
	
	x &= mask
	x |= sign & ~mask
	return x

def add_bit(x, y, carryIn):
	result = 0
	carryOut = 0
	
	if x | 1   == x: # x & 1
		carryOut |= result
		result = ~result
	if y | 1   == y: # y & 1
		carryOut |= result
		result = ~result
	if carryIn == -1:
		carryOut |= result
		result = ~result
	
	return result, carryOut

def add(x, y):
	result = 0
	bit = 1
	carryOut = 0
	mask = 0
	
	while True:
		carryIn = carryOut
		s, carryOut = add_bit(x, y, carryIn)
		if s == -1:
			result |= bit
		
		bit <<= 1
		mask <<= 1
		mask |= 1
		x >>= 1
		y >>= 1
		
		if x == 0:
			if y == 0:
				if carryOut == 0:
					break
				else:
					# There's a carry-out, but both x and y are zero,
					# so the carry-out will be handled in the next
					# loop iteration
					continue
			elif y == -1:
				# The remaining sign bits of the result will be
				# the opposite of carryOut.
				carryOut = ~carryOut
				break
		elif x == -1:
			if y == 0:
				carryOut = ~carryOut
				break
			elif y == -1:
				# The sign bits of x and y are identical,
				# meaning they will cancel each other out during
				# the addition. That means that the sign bits of
				# the result will be set to carryOut
				break
	
	# Copy the sign bits from carryOut onto the result
	result |= carryOut & ~mask
	return result

def neg(x):
	return add(~x, 1)

def mul(x, y):
	result = 0
	sign = 0
	
	if x >> 64 == -1:
		x = neg(x)
		sign = ~sign
	
	if y >> 64 == -1:
		y = neg(y)
		sign = ~sign
	
	while True:
		if y == 0:
			break
		
		if y & 1:
			result = add(result, x)
		
		x <<= 1
		y >>= 1
	
	if sign == -1:
		result = neg(result)
	
	return result

