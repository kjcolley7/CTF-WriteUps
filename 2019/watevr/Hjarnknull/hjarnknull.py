#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import signal

def interrupted(signum, frame):
    print("timeout")
    exit()


signal.signal(signal.SIGALRM, interrupted)
# signal.alarm(20)

code = [None]*30000 # fält som består av [instructions, arguements]
stack = [] # fält med pekare till code
data = [1]*1000 # fält med data element

VERBOSE = False
TESTMODE = True
# challenges = [x.rstrip("\n") for x in open("/home/ctf/challenge_file.txt", "r").readlines()]
current_challenge = 0
fetch_phase = 0
score = 0

def vprint(s, *args, **kwargs):
    if VERBOSE:
        print(s, *args, **kwargs)

#"server sided"
def validate_answare(answare):
    global fetch_phase
    global challenges
    global current_challenge
    global score
    if str(answare) == str(challenges[current_challenge].split(":")[1]):
        score += 1
        current_challenge += 1
    else:
        print("Ledsen asså men ditt program funkar helt enkelt inte :/")
        exit(0)
    if score > 3:
        print("J\xe4vlar vilket klockrent program du har skrivit! H\xe4r har du en flagga " + "".join(open("/home/ctf/flag.txt", "r").readlines()).rstrip("\n"))
        exit(0)
def take_input_from_server():
    global fetch_phase
    global challenges
    global current_challenge
    serv_resp = int(str(challenges[current_challenge].split(":")[0]).split(" ")[fetch_phase]) # ta fetch_phase position från input listan
    if fetch_phase == 2:
        fetch_phase = 0
    else:
        fetch_phase += 1
    return serv_resp

opmap = {
    "eller": "orr",
    "inte": "inv",
    "testa": "jeq",
    "poppa": "ret",
    "in": "rdn",
    "ut": "wrn",
    "hsh": "lsr",
    "vsh": "lsl"
}

scratch_map = {}
def resolve(value):
    try:
        ret = "%s@%d" % (scratch_map[value], value)
    except KeyError:
        ret = str(value)
    
    #print("resolve(%d) -> %s" % (value, ret))
    return ret

#"client sided"
def testexec(ip, endip):
    while ip != endip:
        op = code[ip][0].lower()
        args = code[ip][1]
        # print(ip, opmap[op], args)
        vprint(str(ip) + ": ", end="")
        if op == "eller" or op == "orr":
            x = data[args[0]]
            y = data[args[1]]
            result = x | y
            data[args[0]] = result
            vprint("orr %s (%s), %s (%s) -> %d = %s" % (resolve(args[0]), bin(x), resolve(args[1]), bin(y), result, bin(result)))
        elif op == "inte" or op == "inv":
            x = data[args[0]]
            result = ~x
            data[args[0]] = result
            vprint("inv %s (%s) -> %d = %s" % (resolve(args[0]), bin(x), result, bin(result)))
        elif op == "testa" or op == "jeq":
            x = data[args[0]]
            y = data[args[1]]
            vprint("jeq %s (%s), %s (%s), %d (%s)" % (resolve(args[0]), bin(x), resolve(args[1]), bin(y), args[2], "taken" if x == y else "not taken"))
            if x == y:
                stack.append(ip)
                ip = args[2]
                continue
        elif op == "poppa" or op == "ret":
            ip = stack.pop()
            vprint("ret -> %d" % ip)
        elif op == "in" or op == "rdn":
            vprint("rdn %s" % resolve(args[0]))
            result = int(input())
            data[args[0]] = result
        elif op == "ut" or op == "wrn":
            result = data[args[0]]
            vprint("wrn %s (%s)" % (resolve(args[0]), bin(result)))
            print("OUTPUT>>> " + str(result))
        elif op == "hsh" or op == "lsr":
            x = data[args[0]]
            y = data[args[1]]
            result = x >> y
            vprint("lsr %s (%s), %s (%s) -> %d = %s" % (resolve(args[0]), bin(x), resolve(args[1]), bin(y), result, bin(result)))
            data[args[0]] = result
        elif op == "vsh" or op == "lsl":
            x = data[args[0]]
            y = data[args[1]]
            result = x << y
            vprint("lsl %s (%s), %s (%s) -> %d = %s" % (resolve(args[0]), bin(x), resolve(args[1]), bin(y), result, bin(result)))
            data[args[0]] = result
        ip += 1
def execute(ip, endip):
    while ip != endip:
        op = code[ip][0].lower()
        args = code[ip][1]
        #print(ip, op, args)
        if op == "eller":
            data[args[0]] = data[args[0]] | data[args[1]]
        elif op == "inte":
            data[args[0]] = ~data[args[0]]
        elif op == "testa":
            if data[args[0]] == data[args[1]]:
                stack.append(ip)
                ip = args[2]
                continue
        elif op == "poppa":
            ip = stack.pop()
        elif op == "in":
            data[args[0]] = take_input_from_server()
        elif op == "ut":
            validate_answare(data[args[0]])
        elif op == "hsh":
            data[args[0]] = data[args[0]] >> data[args[1]]
        elif op == "vsh":
            data[args[0]] = data[args[0]] << data[args[1]]
        ip += 1
def main():
    print("Welcome to hj\xe4rnknull!")
    print("Hj\xe4rnknull is the most useful language that has ever been written!")
    print('Syntax: "instruction argument1 argument2 ..."')
    print("valid instructions are: eller, inte, hsh, vsh, testa, poppa, in, ut. End program with slut")
    
    global scratch_map
    try:
        with open("scratch.map", "r") as scratch_fp:
            for line in scratch_fp:
                value, name = line.strip().split("=")
                scratch_map[int(value)] = name
    except Exception as e:
        print(e)
    
    loc = 0
    while True:
        # tmpcode = str(input(str(loc) + ": ")).split(" ")
        tmpcode = str(input()).split(" ")
        code[loc] = [tmpcode[0], [int(x) for x in tmpcode[1:]]]
        if "slut" in str(code):
            break;
        loc += 1
        if loc % 1000 == 0:
            print("ip = %d" % loc)
    
    print("program loaded!")
    
    if TESTMODE:
        testexec(0, loc)
    else:
        execute(0, loc)
main()
