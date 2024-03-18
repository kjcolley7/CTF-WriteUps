import z3
import ast
import re
from abc import ABC, abstractmethod
from typing import Optional, Union, TypeAlias


Signal: TypeAlias = Union[bool, z3.BoolRef]
Driver: TypeAlias = Union['LogicComponent', str]


class Circuit:
	components: dict[str, 'LogicComponent']
	
	def __init__(self):
		self.components = {}
	
	def add[T: 'LogicComponent'](self, component: T, label: Optional[str] = None) -> T:
		if isinstance(component, Gate):
			for x in component.inputs:
				assert x in self.components.values()
		
		if label is not None:
			component.label = label
		else:
			label = component.label
		
		assert label is not None
		
		assert label not in self.components, label
		self.components[label] = component
		return component
	
	def wire(self, driver: Driver, label: Optional[str] = None) -> 'Wire':
		if label is None:
			label = f'wire_{driver if isinstance(driver, str) else driver.label}'
		
		try:
			wire = self.lookup(label)
			assert isinstance(wire, Wire)
			return wire
		except KeyError:
			return self.add(Wire(driver=driver), label=label)
	
	def lookup(self, driver: Optional['Driver']) -> 'LogicComponent':
		assert driver is not None
		if isinstance(driver, LogicComponent):
			return driver
		return self.components[driver]
	
	def link(self) -> None:
		for c in self.components.values():
			c.link(self)
	
	def rst(self) -> None:
		for c in self.components.values():
			c.rst()
	
	def propagate(self) -> None:
		for c in self.components.values():
			c.propagate()
	
	def clk(self) -> None:
		for c in self.components.values():
			c.clk()
	
	def tick(self) -> None:
		self.propagate()
		self.clk()


class LogicComponent(ABC):
	label: Optional[str]
	
	def __init__(self, label=None):
		self.label = label
	
	def __repr__(self) -> str:
		return f'{self.label} = {self.__class__.__name__}()'
	
	def link(self, circuit: Circuit) -> None:
		pass
	
	def rst(self) -> None:
		pass
	
	def clk(self) -> None:
		pass
	
	def propagate(self) -> None:
		pass
	
	@abstractmethod
	def value(self) -> Signal:
		...


class Wire(LogicComponent):
	driver: Optional[Driver]
	
	def __init__(self, driver: Optional[Driver] = None, **kwargs):
		super().__init__(**kwargs)
		self.driver = driver
	
	def __repr__(self) -> str:
		if isinstance(self.driver, str):
			drv = repr(self.driver)
		elif isinstance(self.driver, LogicComponent):
			drv = repr(self.driver.label or self.driver)
		else:
			drv = "None"
		return f'{self.label} = {self.__class__.__name__}(driver={drv})'
	
	def link(self, circuit: Circuit) -> None:
		self.driver = circuit.lookup(self.driver)
	
	def value(self) -> Signal:
		assert isinstance(self.driver, LogicComponent), f'{repr(self)}'
		return self.driver.value()


class Gate(LogicComponent):
	inputs: list[LogicComponent]
	
	def __init__(self, *inputs: LogicComponent, **kwargs):
		super().__init__(**kwargs)
		self.inputs = list(inputs)
	
	def __repr__(self) -> str:
		return f'{self.label} = {self.__class__.__name__}({", ".join(x.label or "None" for x in self.inputs)})'
	
	@staticmethod
	@abstractmethod
	def combine(*inputs: Signal) -> Signal:
		...
	
	def value(self) -> Signal:
		return self.combine(*[x.value() for x in self.inputs])


class AndGate(Gate):
	@staticmethod
	def combine(*inputs: Signal) -> Signal:
		if all(isinstance(x, bool) for x in inputs):
			return all(inputs)
		
		r = z3.And(inputs)
		assert isinstance(r, z3.BoolRef)
		return r


class OrGate(Gate):
	@staticmethod
	def combine(*inputs: Signal) -> Signal:
		if all(isinstance(x, bool) for x in inputs):
			return any(inputs)
		
		r = z3.Or(inputs)
		assert isinstance(r, z3.BoolRef)
		return r


class XorGate(Gate):
	@staticmethod
	def combine(*inputs: Signal) -> Signal:
		assert len(inputs) == 2
		a, b = inputs
		
		if isinstance(a, bool) and isinstance(b, bool):
			return a ^ b
		
		return z3.Xor(a, b)


class NotGate(Gate):
	@staticmethod
	def combine(*inputs: Signal) -> Signal:
		assert len(inputs) == 1
		x = inputs[0]
		
		if isinstance(x, bool):
			return not x
		
		r = z3.Not(x)
		assert isinstance(r, z3.BoolRef)
		return r


class FlipFlop(LogicComponent):
	preset: Signal
	din: Optional[LogicComponent]
	next: Optional[Signal]
	dout: Optional[Signal]
	
	def __init__(self, preset: Signal = False, **kwargs):
		super().__init__(**kwargs)
		self.preset = preset
		self.rst()
	
	def __repr__(self) -> str:
		return f'{self.label} = {self.__class__.__name__}(din={self.din and self.din.label or self.din})'
	
	def rst(self) -> None:
		self.next = None
		self.dout = self.preset
	
	def propagate(self) -> None:
		assert self.din is not None
		self.next = self.din.value()
	
	def clk(self) -> None:
		assert self.next is not None
		self.dout = self.next
		self.next = None
	
	def value(self) -> Signal:
		assert self.dout is not None
		return self.dout


class Switch(LogicComponent):
	state: Optional[Signal] = None
	
	def __init__(self, signal: Optional[Signal] = None, **kwargs):
		super().__init__(**kwargs)
		self.state = signal
	
	def set(self, state: Signal) -> None:
		self.state = state
	
	def value(self) -> Signal:
		assert self.state is not None
		return self.state


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


def cpld_to_py(s: str) -> ast.expr:
	pys = (
		s.replace("!", "~")
		 .replace("$", "^")
	)
	stmt = ast.parse(pys).body[0]
	assert isinstance(stmt, ast.Expr)
	return stmt.value

def ast_to_circuit(circuit: Circuit, expr: ast.expr) -> LogicComponent:
	if isinstance(expr, ast.Name):
		return circuit.wire(expr.id)
	
	if isinstance(expr, ast.UnaryOp):
		assert isinstance(expr.op, ast.Invert)
		operand = ast_to_circuit(circuit, expr.operand)
		gate = NotGate(operand)
		return circuit.add(gate, label=f'not_{operand.label or id(gate)}')
	elif isinstance(expr, ast.BinOp):
		a = ast_to_circuit(circuit, expr.left)
		b = ast_to_circuit(circuit, expr.right)
		if isinstance(expr.op, ast.BitXor):
			gate = XorGate(a, b)
			gate.label = f'xor_{id(gate)}'
		else:
			assert isinstance(expr.op, ast.BitAnd)
			gate = AndGate(a, b)
			gate.label = f'and_{id(gate)}'
		return circuit.add(gate)
	else:
		raise TypeError(f"Unexpected expr type: {repr(expr)}")

def parse_cpld(circuit: Circuit, s: str) -> LogicComponent:
	ast = cpld_to_py(s)
	return ast_to_circuit(circuit, ast)


with open("PALWORLD.PLD") as fp:
	src = fp.read()

def clean_whitespace(s: str) -> str:
	return re.sub(r'\s+', " ", s)

circuit = Circuit()
assignments: list[tuple[str, str]] = re.findall(r'^([a-zA-Z_][a-zA-Z0-9_]*(?:.[A-Z]+)?)\s*=\s*([^;]+);', src, re.MULTILINE)
for name, expr in assignments:
	if name == "PIN":
		continue
	
	if "." in name and not name.endswith("D"):
		continue
	
	comp = parse_cpld(circuit, expr)
	
	if name.endswith(".D"):
		ff = FlipFlop()
		ff.din = comp
		circuit.add(ff, name[:-2])
	else:
		circuit.wire(comp, label=name)

for name, expr in assignments:
	if not name.endswith(".AP"):
		continue
	
	if expr != "reset":
		continue
	
	ff = circuit.lookup(name[:-3])
	assert isinstance(ff, FlipFlop)
	ff.preset = True
	ff.rst()

flag_in = [circuit.add(Switch(label=f'flag_in{i}')) for i in range(8)]

def set_flag_byte(symbyte: SymByte):
	for i in range(8):
		flag_in[i].set(symbyte.bits[i])

circuit.link()

for name, comp in circuit.components.items():
	# print(comp)
	
	if not isinstance(comp, Wire):
		continue
	
	assert isinstance(comp.driver, LogicComponent), f'{repr(comp)}'

solver = z3.Solver()
flag_ok = circuit.components["flag_ok"]

flag: list[SymByte] = []
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

# print(z3.simplify(flag_ok.value() == True))
model = solver.model()
flag_str = b"".join(f.value(model).to_bytes() for f in flag)
print(flag_str)
