def add_bad(x, y_arg):
	add_return_y = symbol("add_return_y")
	add_check_y_zero = symbol("add_check_y_zero")
	add_loop_cond = symbol("add_loop_cond")
	add_x_carryin_false = symbol("add_x_carryin_false")
	add_x_y_carryin_false = symbol("add_x_y_carryin_false")
	add_x_bit_zero = symbol("add_x_bit_zero")
	add_not_x_carryin_false = symbol("add_not_x_carryin_false")
	add_not_x_y_carryin_false = symbol("add_not_x_y_carryin_false")
	add_after_addone = symbol("add_after_addone")
	add_after_loop = symbol("add_after_loop")
	add_carryout_false = symbol("add_carryout_false")
	add_x_not_sign = symbol("add_x_not_sign")
	add_y_not_sign = symbol("add_y_not_sign")
	add_return_x = symbol("add_return_x")
	
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
		jmp(add_check_y_zero) +
		
	label(add_return_y) +
		mov(x, y) +
		jmp(add_return_x) +
		
	label(add_check_y_zero) +
		jeq(y, 0, add_return_x) +
		
		zero(carryOut) +
		
	label(add_loop_cond) +
		# jeq(bit, 165, add_after_loop) +
		jeq(bit, 19, add_after_loop) +
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
							jmp(add_after_addone) +
						# else:
						label(add_x_y_carryin_false) +
							bit_and(x, notbit) +
							mov(carryOut, 1) +
							jmp(add_after_addone) +
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
					jmp(add_after_addone) +
				#else:
				label(add_not_x_y_carryin_false) +
					orr(x, bit) +
			
		label(add_after_addone) +
			lsl(bit, 1) +
			lsl(mask, 1) +
			orr(mask, 1) +
			jmp(add_loop_cond) +
		
	label(add_after_loop) +
		zero(sign) +
		
		# if not carryOut:
		jeq(carryOut, 0, add_carryout_false) +
			inv(sign) +
		
	label(add_carryout_false) +
		mov(tmp, x) +
		# bit_and(tmp, 165) +
		bit_and(tmp, 19) +
		
		# if x & (1 << 65):
		jeq(tmp, 0, add_x_not_sign) +
			inv(sign) +
		
	label(add_x_not_sign) +
		mov(tmp, y) +
		# bit_and(tmp, 165) +
		bit_and(tmp, 19) +
		
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