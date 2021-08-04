0x0000: add     R29, ZERO, 0x200
0x0001: movt    R1, 0x20 (' ')
0x0002: movb    R1, 0x3a (':')
0x0003: sub     R29, R29, 0x1
0x0004: str     R1, [R29+ZERO]
0x0005: movt    R1, 0x64726f ('ord')
0x0006: movb    R1, 0x77 ('w')
0x0007: sub     R29, R29, 0x1
0x0008: str     R1, [R29+ZERO]
0x0009: movt    R1, 0x737361 ('ass')
0x000a: movb    R1, 0x50 ('P')
0x000b: sub     R29, R29, 0x1
0x000c: str     R1, [R29+ZERO]
0x000d: add     R1, ZERO, 0x1
0x000e: orrs    R2, R1, ZERO
0x000f: orrs    R3, R29, ZERO
0x0010: add     R4, ZERO, 0xa
0x0011: syscall                         # printf("Password: ")
0x0012: xor     R1, R1, R1
0x0013: orrs    R2, R1, ZERO
0x0014: add     R3, ZERO, 0x100
0x0015: add     R4, ZERO, 0x18
0x0016: syscall                         # read(STDIN_FILENO, 0x100, 0x18)
0x0017: add     R29, ZERO, 0x200        # Start building password in memory
0x0018: movt    R1, 0x321695 ('2')
0x0019: movb    R1, 0x3e ('>')
0x001a: sub     R29, R29, 0x1
0x001b: str     R1, [R29+ZERO]
0x001c: movt    R1, 0x2740af ('@'')
0x001d: movb    R1, 0x39 ('9')
0x001e: sub     R29, R29, 0x1
0x001f: str     R1, [R29+ZERO]
0x0020: movt    R1, 0x7768c5 ('hw')
0x0021: movb    R1, 0x3c ('<')
0x0022: sub     R29, R29, 0x1
0x0023: str     R1, [R29+ZERO]
0x0024: movt    R1, 0x4c6ac1 ('jL')
0x0025: movb    R1, 0x20 (' ')
0x0026: sub     R29, R29, 0x1
0x0027: str     R1, [R29+ZERO]
0x0028: movt    R1, 0x290dab (')')
0x0029: movb    R1, 0x4e ('N')
0x002a: sub     R29, R29, 0x1
0x002b: str     R1, [R29+ZERO]
0x002c: movt    R1, 0x4176a0 ('vA')
0x002d: movb    R1, 0x5e ('^')
0x002e: sub     R29, R29, 0x1
0x002f: str     R1, [R29+ZERO]
0x0030: xor     ZERO, ZERO, R5
0x0031: movt    R6, 0x1337f0 ('7')      # Value XORed against each DWORD in the password
0x0032: movb    R6, 0xd


validate_password:
0x0033: cmp     R29, 0x200
0x0034: jeq     check_if_matched

0x0035: ldr     R4, [R29+ZERO]
0x0036: add     R29, R29, 0x1
0x0037: xor     R4, R4, R6
0x0038: ldr     R2, [R3+ZERO]
0x0039: add     R3, R3, 0x1
0x003a: cmp     R4, R2
0x003b: jeq     validate_password


invalid_password:
0x003c: movb    R5, 0x1
0x003d: jmp     validate_password


check_if_matched:
0x003e: cmp     R5, ZERO
0x003f: jeq     print_congratulations


print_wrong_password:
0x0040: movb    R29, 0x200
0x0041: movt    R1, 0xa2e64 ('d.')
0x0042: movb    R1, 0x72 ('r')
0x0043: sub     R29, R29, 0x1
0x0044: str     R1, [R29+ZERO]
0x0045: movt    R1, 0x6f7773 ('swo')
0x0046: movb    R1, 0x73 ('s')
0x0047: sub     R29, R29, 0x1
0x0048: str     R1, [R29+ZERO]
0x0049: movt    R1, 0x617020 (' pa')
0x004a: movb    R1, 0x67 ('g')
0x004b: sub     R29, R29, 0x1
0x004c: str     R1, [R29+ZERO]
0x004d: movt    R1, 0x6e6f72 ('ron')
0x004e: movb    R1, 0x57 ('W')
0x004f: sub     R29, R29, 0x1
0x0050: str     R1, [R29+ZERO]
0x0051: add     R1, ZERO, 0x1
0x0052: orrs    R2, R1, ZERO
0x0053: orrs    R3, R29, ZERO
0x0054: add     R4, ZERO, 0x10
0x0055: syscall
0x0056: add     R2, ZERO, 0x1
0x0057: jmp     exit


print_congratulations:
0x0058: movb    R29, 0x200
0x0059: add     R1, ZERO, 0xa
0x005a: sub     R29, R29, 0x1
0x005b: str     R1, [R29+ZERO]
0x005c: movt    R1, 0x21736e ('ns!')
0x005d: movb    R1, 0x6f ('o')
0x005e: sub     R29, R29, 0x1
0x005f: str     R1, [R29+ZERO]
0x0060: movt    R1, 0x697461 ('ati')
0x0061: movb    R1, 0x6c ('l')
0x0062: sub     R29, R29, 0x1
0x0063: str     R1, [R29+ZERO]
0x0064: movt    R1, 0x757461 ('atu')
0x0065: movb    R1, 0x72 ('r')
0x0066: sub     R29, R29, 0x1
0x0067: str     R1, [R29+ZERO]
0x0068: movt    R1, 0x676e6f ('ong')
0x0069: movb    R1, 0x43 ('C')
0x006a: sub     R29, R29, 0x1
0x006b: str     R1, [R29+ZERO]
0x006c: add     R1, ZERO, 0x1
0x006d: orrs    R2, R1, ZERO
0x006e: orrs    R3, R29, ZERO
0x006f: add     R4, ZERO, 0x11
0x0070: syscall
0x0071: xor     R2, R2, R2


exit:
0x0072: add     R1, ZERO, 0x2
0x0073: syscall

