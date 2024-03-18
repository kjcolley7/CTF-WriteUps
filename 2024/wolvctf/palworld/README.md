# [REV 500] palworld (2 solves)

Challenge author: HCAdam

> We have Palworld at home. Palworld at home:

-----

## Part 1: First look, initial guesses

After skimming through the attached [PALWORLD.PLD](PALWORLD.PLD) file,
it is obviously some sort of a textual circuit description file. Here's a
snippet from the beginning:

```
/* WE HAVE PALWORLD AT HOME. PALWORLD AT HOME: */

PIN    = clk;
PIN    = reset;
PIN    = flag_in0;
PIN    = flag_in1;
PIN    = flag_in2;
PIN    = flag_in3;
PIN    = flag_in4;
PIN    = flag_in5;
PIN    = flag_in6;
PIN    = flag_in7;
PIN    = flag_ok;

PINNODE      = JTCN294;
PINNODE      = JTCN295;
```

Even before understanding the file format, we can see that it's defining a
synchronous (clocked) circuit that takes in one byte of a flag at a time
and provides a single output: `flag_ok`. The goal of this challenge then
must be to clock in some series of flag bytes that results in the `flag_ok`
pin being pulled high.

The `flag_ok` pin is driven by combinatorial logic, the first 4 lines (of 70!)
look like this:

```
flag_ok = ( ( ( ( ( JTCN294 & ! ( AGEB1 ) ) & ( ( ! ( SDFK2 ) & ! ( SDFK4
  ) ) & ( ! ( SDFK8 ) & ! ( SDFK9 ) ) ) ) & ( ( ( ( ! ( SDFK15 ) & ! (
  SDFK17 ) ) & ( ! ( SDFK18 ) & ! ( SDFK20 ) ) ) & ( ( ! ( SDFK10
  ) & ! ( SDFK11 ) ) & ( ! ( SDFK13 ) & ! ( SDFK14 ) ) ) ) & ( ( ( ! (
...
```

Later on in the file, we can also see where the flag input bits are being
used:

```
JTCN307 = ( flag_in0 $ SWTE0 );
JTCN308 = ( flag_in1 $ SWTE1 );
JTCN309 = ( SWTE2 $ flag_in2 );
JTCN310 = ( SWTE3 $ flag_in3 );
JTCN311 = ( SWTE4 $ flag_in4 );
JTCN312 = ( flag_in5 $ SWTE5 );
JTCN313 = ( flag_in6 $ SWTE6 );
JTCN314 = ( flag_in7 $ SWTE7 );
```

The `$` operator is a mystery to me for now. Let's keep looking through
the file though. Here's another interesting section:

```
AGEB0.AP = 'b'0;
AGEB0.AR = reset;
AGEB0.CK = clk;
AGEB0.D = JTCN294;
AGEB1.AP = 'b'0;
AGEB1.AR = reset;
AGEB1.CK = clk;
AGEB1.D = ( AGEB0 $ AGEB1 );
AGEB2.AP = 'b'0;
AGEB2.AR = reset;
AGEB2.CK = clk;
AGEB2.D = ( AGEB2 $ JTCN369 );
AGEB3.AP = 'b'0;
AGEB3.AR = reset;
AGEB3.CK = clk;
AGEB3.D = ( AGEB3 $ JTCN368 );
AGEB4.AP = 'b'0;
AGEB4.AR = reset;
AGEB4.CK = clk;
AGEB4.D = ( AGEB4 $ ( AGEB3 & JTCN368 ) );
```

This seems to be defining a set of 5 D-flip-flops. There are a bunch more
flip-flops defined throughout the file. Okay, it's time to do some research
to figure out what this file format is.


## Part 2: Google is your friend

After googling the `PINNODE` keyword and helping Google out by throwing in
some words like "circuit description" or "verilog", it comes up with something
called WinCUPL, which is some old circuit description tool that only supports
Windows XP. Setting up a WinXP VM to get the tooling for this running sounds
like a pain, so I decided to solve it statically instead.

Luckily, my searching brought up some documentation of the syntax. Here's the
best resources I found:

* https://ww1.microchip.com/downloads/en/DeviceDoc/doc0737.pdf
* https://class.ece.uw.edu/475/peckol/doc/cupl.html
* https://ece-classes.usc.edu/ee459/library/documents/CUPL_Reference.pdf

There's also a ["VS Cupl" extension](https://marketplace.visualstudio.com/items?itemName=VaynerSystems.VS-Cupl)
for VSCode that provides syntax highlighting for this file format.

Now that we have this documentation, my earlier assumptions about circuit pins
and flip-flops is confirmed. It also answers what the `$` operator is: XOR!
This file seems to only use NOT, AND, and XOR operators, which simplifies things.


## Part 3: Manual circuit reverse engineering

At this point, I started manually reversing the circuit description file. As I
was understanding things, I renamed the "variables" and all references to them.
I also removed useless information, like the `PINNODE` declarations and any lines
setting the flip-flops' clock and reset lines to the clock and reset signals.

The result of my manual reversing is here: [PALWORLD.PLD.edit](PALWORLD.PLD.edit).


## Part 4: Using Z3 to solve for `flag_ok`

I realized that reversing this by hand would take too much manual effort, so I
decided to write some tooling to automate this for me. My first thought was if
I can parse this file format, I can then use Microsoft's Z3 solver to solve the
`flag_ok` expression. Also, the expression syntax is close enough to Python
syntax, so by some careful find/replace, it then becomes parsable as Python code:

```python
def clean_whitespace(s: str) -> str:
	return re.sub(r'\s+', " ", s)

def cpld_to_py(s: str) -> ast.expr:
	pys = (
		s.replace("!", "~")
		 .replace("$", "^")
	)
	stmt = ast.parse(pys).body[0]
	assert isinstance(stmt, ast.Expr)
	return stmt.value

with open("PALWORLD.PLD") as fp:
	src = fp.read()

flag_expr = re.findall(r'flag_ok = ([^;]+);', src, re.MULTILINE)[0]
flag_expr = clean_whitespace(flag_expr)

flag_ast = cpld_to_py(flag_expr)
```

From some interactive exploration of the produced AST structure, we can see that
it worked:

```python
>>> flag_ast
<ast.BoolOp object at 0x1028ebf70>
>>> dir(flag_ast)
['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__match_args__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_attributes', '_fields', 'col_offset', 'end_col_offset', 'end_lineno', 'lineno', 'op', 'values']
>>> flag_ast.op
<ast.And object at 0x10281b280>
>>> flag_ast.values
[<ast.BoolOp object at 0x1028ebf40>, <ast.BoolOp object at 0x1028e8f40>]
```

After this, I wrote some code to walk this AST and convert it to a Z3 expression.
`ast.BitAnd` -> `z3.And`, `ast.BitXor` -> `z3.Xor`, and `ast.Invert` -> `z3.Not`.
Then, make a `z3.Solver` and do `solver.add(flag_ok == True)`, and after checking
as `sat` you can get a model! Sadly, that model isn't very useful, as it just tells
you what the internal state of the circuit needs to be for `flag_ok` to be true,
not the inputs needed to get there. However, this result was encouraging, so I
decided to take this further.


## Part 5: Building a symbolic execution engine for circuit logic

Yes, you read that right. I figured that since traditional symbolic execution
works well for many reverse engineering challenges and effectively works by
emulating code while building up constraints for a SAT solver like Z3, I could
do the same thing for a circuit. So anyway, I started ~~blasting~~ writing Python.
There's too much code for me to put it all in the writeup, so instead I'll share
some snippets. I wrote Python code for simulating circuits, using `Signal` values
which can either be Python's `bool` type or a `z3.BoolRef`. Here's the logic for
simulating an AND gate:

```python
class AndGate(Gate):
	@staticmethod
	def combine(*inputs: Signal) -> Signal:
		if all(isinstance(x, bool) for x in inputs):
			return all(inputs)
		
		r = z3.And(inputs)
		assert isinstance(r, z3.BoolRef)
		return r
```

This tries to keep everything concrete for as long as possible, but as soon as
one of the inputs is symbolic (is a `z3.BoolRef` instead of `bool`), then it must
be affected by one of the flag bits. That's when the output from the gate becomes
symbolic. I also created a `SymByte` type (symbolic byte), which is how I represent
the flag bytes:

```python
class SymByte:
	bits: list[z3.BoolRef]
	
	def __init__(self, name: str):
		self.bits = [z3.Bool(f'{name}_{i}') for i in range(8)]
	
	def value(self, model: z3.ModelRef) -> int:
		x = 0
		for i, b in enumerate(self.bits):
			bit = bool(model[b])
			assert isinstance(bit, bool)
			x |= bit << i
		return x
```

This creates a list of 8 symbolic boolean values, one for each bit of the byte.
The `value()` method allows getting the concrete value of the byte after Z3 has
produced a model that satisfies all constraints. This is how I'll be able to show
the flag once it's solved. And here's flag bytes are input:

```python
flag_in = [circuit.add(Switch(label=f'flag_in{i}')) for i in range(8)]

def set_flag_byte(symbyte: SymByte):
	for i in range(8):
		flag_in[i].set(symbyte.bits[i])
```

This code creates 8 `Switch` objects (which is how I define input pins), and the
`set_flag_byte` function applies the symbolic bits from a `SymByte` to the switches.

The parsing code I wrote earlier for parsing the `flag_ok` expr had to be upgraded
to handle ALL "variables" and to understand flip-flops.

At this point, the main loop is pretty easy:

```python
solver = z3.Solver()
flag_ok = circuit.components["flag_ok"]

flag: list[SymByte] = []
while True:
	print(f"Entering byte {len(flag)}...")
	
	next_byte = SymByte(f'flag{len(flag)}')
	flag.append(next_byte)
	set_flag_byte(next_byte)
	circuit.tick()
	
	solver.push()
	solver.add(flag_ok.value() == True)
	if solver.check() == z3.sat:
		break
	print("unsat")
	solver.pop()
```

This code builds up a list of flag bytes as it goes. It starts by entering in the
first flag byte, simulating the circuit for one tick (full clock cycle), and then
checking if the `flag_ok` output signal can possibly be True given the constraints.
If not, we need to remove that `flag_ok.value() == True` constraint, as after the
next byte is input, `flag_ok.value()` will create a different constraint tree.
Eventually, when the correct number of bytes have been input, the solver returns
`sat`, indicating that it found a solution to satisfy all the constraints. Now we
just need to print out the constraints:

```python
model = solver.model()
flag_str = b"".join(f.value(model).to_bytes() for f in flag)
print(flag_str)
```

And this should solve the challenge, right?

```python
(venv) #kMacA:~/ctf/24/wolv/palworld$ python solve.py 
Entering byte 0...
unsat
Entering byte 1...
unsat
Entering byte 2...
unsat
Entering byte 3...
unsat
...
Entering byte 30...
unsat
Entering byte 31...
b'@\r\xa8\xde2\xffE\x08\xb9\xd33\x88\xa4\x85\xbd\xc5!\xfd\x7fi \xe0zXV\x00\xba\xac\xe4O\x08\xaf'
```

Hmm, not quite. After some head scratching and looking through my edited version
of the circuit description file, I noticed something. At the end of the file is a
description of 16 flip-flops. These flip-flops are used a lot for mangling the flag
bits. When I was manually reverse engineering it, I was confused by this, as it
appears to me that all of the flip-flops are initialized to zero. Then, they are
effectively rotated around, some of them attempting to XOR the previous value with
a later value. However, if they're all zero at first, then `0 ^ 0 == 0`, so the bits
will remain false throughout the entire circuit simulation. Is this right?

One thing that I didn't notice before stood out after I simplified the file by removing
the obvious flip-flop structural lines (setting the flip-flop's clock signal, reset
signal, preset value to 0). Some of these 16 flip-flops have their `.AP` and `.AR` fields
swapped! This means that the initial value of these flip-flops won't be 0, but instead the
`reset` signal is used as the preset value. Assuming the circuit starts in reset, this
means that these flip-flops will have an initial value of 1 instead of 0. Accounting for
this in the code (after parsing and building the circuit description):

```python
for name, expr in assignments:
	if not name.endswith(".AP"):
		continue
	
	if expr != "reset":
		continue
	
	ff = circuit.lookup(name[:-3])
	assert isinstance(ff, FlipFlop)
	ff.preset = True
	ff.rst()
```

This finds any flip-flops with `<name>.AP = reset;`, and then it changes their `preset`
value to True and resets them (so they are outputting a True signal initially). Let's
also print out the value of this "rotating" 16-bit integer before inputting each byte:

```python
# In main loop
while True:
	print(f"Entering byte {len(flag)}...")
	
	rotating = 0
	for i in range(16):
		try:
			ff = circuit.lookup(f'rotating{i}')
		except KeyError:
			ff = circuit.lookup(f'SWTE{i}')
		assert isinstance(ff, FlipFlop)
		assert isinstance(ff.dout, bool)
		rotating |= ff.dout << i
	print(f"Rotating: 0b{bin(rotating)[2:].rjust(16, '0')}")
	...
```

And let's run the updated solver script:

```python
(venv) #kMacA:~/ctf/24/wolv/palworld$ python solve.py 
Entering byte 0...
Rotating: 0b0001001100110111
unsat
Entering byte 1...
Rotating: 0b0010011001101110
unsat
Entering byte 2...
Rotating: 0b0100110011011100
unsat
Entering byte 3...
Rotating: 0b1001100110111000
unsat
Entering byte 4...
Rotating: 0b0011001101001001
unsat
Entering byte 5...
Rotating: 0b0110011010010010
unsat
Entering byte 6...
Rotating: 0b1100110100100100
unsat
Entering byte 7...
Rotating: 0b1001101001110001
unsat
Entering byte 8...
Rotating: 0b0011010011011011
unsat
Entering byte 9...
Rotating: 0b0110100110110110
unsat
Entering byte 10...
Rotating: 0b1101001101101100
unsat
Entering byte 11...
Rotating: 0b1010011011100001
unsat
Entering byte 12...
Rotating: 0b0100110111111011
unsat
Entering byte 13...
Rotating: 0b1001101111110110
unsat
Entering byte 14...
Rotating: 0b0011011111010101
unsat
Entering byte 15...
Rotating: 0b0110111110101010
unsat
Entering byte 16...
Rotating: 0b1101111101010100
unsat
Entering byte 17...
Rotating: 0b1011111010010001
unsat
Entering byte 18...
Rotating: 0b0111110100011011
unsat
Entering byte 19...
Rotating: 0b1111101000110110
unsat
Entering byte 20...
Rotating: 0b1111010001010101
unsat
Entering byte 21...
Rotating: 0b1110100010010011
unsat
Entering byte 22...
Rotating: 0b1101000100011111
unsat
Entering byte 23...
Rotating: 0b1010001000000111
unsat
Entering byte 24...
Rotating: 0b0100010000110111
unsat
Entering byte 25...
Rotating: 0b1000100001101110
unsat
Entering byte 26...
Rotating: 0b0001000011100101
unsat
Entering byte 27...
Rotating: 0b0010000111001010
unsat
Entering byte 28...
Rotating: 0b0100001110010100
unsat
Entering byte 29...
Rotating: 0b1000011100101000
unsat
Entering byte 30...
Rotating: 0b0000111001101001
unsat
Entering byte 31...
Rotating: 0b0001110011010010
b'wctf{maybe_i_should_use_an_fpga}'
```

Boom, solved! Here's the full solution script: [solve.py](solve.py)


## Conclusion

I really enjoyed working on this challenge. It's the first time I ever wrote
any form of symbolic execution engine, and I learned a lot about Z3 doing so.
I probably could have solved this challenge quicker if I spent the time I used
to write the symbolic execution engine on manual reverse engineering instead,
but this way was much more enjoyable and resulted in me learning more. Overall,
I think this was a really well-designed challenge: an obvious goal, not guessy,
just the right level of difficulty. Thanks to HCAdam for the challenge!
