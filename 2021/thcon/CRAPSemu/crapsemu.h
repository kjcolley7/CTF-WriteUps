/*
   This file has been generated by IDA.
   It contains local type definitions from
   crapsemu.i64
*/

#define __int8 char
#define __int16 short
#define __int32 int
#define __int64 long long

/* 1 */
enum Register
{
  ZERO = 0x0,
  Register_01 = 0x1,
  Register_02 = 0x2,
  Register_03 = 0x3,
  Register_04 = 0x4,
  Register_05 = 0x5,
  Register_06 = 0x6,
  Register_07 = 0x7,
  Register_08 = 0x8,
  Register_09 = 0x9,
  Register_0A = 0xA,
  Register_0B = 0xB,
  Register_0C = 0xC,
  Register_0D = 0xD,
  Register_0E = 0xE,
  Register_0F = 0xF,
  Register_10 = 0x10,
  Register_11 = 0x11,
  Register_12 = 0x12,
  Register_13 = 0x13,
  Register_14 = 0x14,
  TMP = 0x15,
  Register_16 = 0x16,
  Register_17 = 0x17,
  Register_18 = 0x18,
  Register_19 = 0x19,
  Register_1A = 0x1A,
  Register_1B = 0x1B,
  Register_1C = 0x1C,
  Register_1D = 0x1D,
  PC = 0x1E,
  FETCH = 0x1F,
};

/* 2 */
enum Opcode
{
  Opcode_ADD = 0x0,
  Opcode_AND = 0x1,
  Opcode_ORR = 0x2,
  Opcode_XOR = 0x3,
  Opcode_SUB = 0x4,
  Opcode_05 = 0x5,
  Opcode_06 = 0x6,
  Opcode_07 = 0x7,
  Opcode_08 = 0x8,
  Opcode_09 = 0x9,
  Opcode_0A = 0xA,
  Opcode_0B = 0xB,
  Opcode_0C = 0xC,
  Opcode_SHR = 0xD,
  Opcode_SHL = 0xE,
  Opcode_0F = 0xF,
  Opcode_ADDS = 0x10,
  Opcode_ANDS = 0x11,
  Opcode_ORRS = 0x12,
  Opcode_XORS = 0x13,
  Opcode_SUBS = 0x14,
  Opcode_15 = 0x15,
  Opcode_16 = 0x16,
  Opcode_17 = 0x17,
  Opcode_18 = 0x18,
  Opcode_19 = 0x19,
  Opcode_1A = 0x1A,
  Opcode_1B = 0x1B,
  Opcode_1C = 0x1C,
  Opcode_1D = 0x1D,
  Opcode_1E = 0x1E,
  Opcode_1F = 0x1F,
  Opcode_X13 = 0x20,
  Opcode_X25 = 0x21,
  Opcode_22 = 0x22,
  Opcode_SL8 = 0x23,
  Opcode_24 = 0x24,
  Opcode_25 = 0x25,
  Opcode_26 = 0x26,
  Opcode_27 = 0x27,
  Opcode_NOP = 0x28,
  Opcode_29 = 0x29,
  Opcode_2A = 0x2A,
  Opcode_2B = 0x2B,
  Opcode_2C = 0x2C,
  Opcode_2D = 0x2D,
  Opcode_2E = 0x2E,
  Opcode_2F = 0x2F,
  Opcode_30 = 0x30,
  Opcode_31 = 0x31,
  Opcode_32 = 0x32,
  Opcode_33 = 0x33,
  Opcode_34 = 0x34,
  Opcode_35 = 0x35,
  Opcode_36 = 0x36,
  Opcode_37 = 0x37,
  Opcode_38 = 0x38,
  Opcode_39 = 0x39,
  Opcode_3A = 0x3A,
  Opcode_3B = 0x3B,
  Opcode_3C = 0x3C,
  Opcode_3D = 0x3D,
  Opcode_3E = 0x3E,
  Opcode_3F = 0x3F,
};

/* 3 */
enum Flags : __int8
{
  Flag_VF = 0x1,
  Flag_CF = 0x2,
  Flag_ZF = 0x4,
  Flag_SF = 0x8,
};

/* 4 */
enum Cond
{
  Cond_0 = 0x0,
  Cond_EQUAL_or_ZERO = 0x1,
  Cond_SIGNED_LESS_OR_EQUAL = 0x2,
  Cond_LESS = 0x3,
  Cond_SIGNED_LESS_OR_EQUAL_again = 0x4,
  Cond_OVERFLOW = 0x5,
  Cond_NEGATIVE = 0x6,
  Cond_CARRY_SET = 0x7,
  Cond_ALWAYS = 0x8,
  Cond_NOT_EQUAL_or_ZERO = 0x9,
  Cond_SIGNED_GREATER = 0xA,
  Cond_GREATER_OR_EQUAL = 0xB,
  Cond_SIGNED_GREATER_again = 0xC,
  Cond_NOT_OVERFLOW = 0xD,
  Cond_NOT_NEGATIVE = 0xE,
  Cond_CARRY_CLEAR = 0xF,
};

