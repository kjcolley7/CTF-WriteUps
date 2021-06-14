#!/usr/bin/python3

# requirements: python3 -m pip install pyte

import re, pyte, subprocess, sys


def execute(cmd):

    proc=subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, )

    output=proc.communicate()[0].decode().replace('\n','\n\r')

    return output


if len(sys.argv) != 2:

    exit("Usage:\n  python ./chall.py script.py")


if re.match("\/tmp\/\w*",sys.argv[1]):

    script = sys.argv[1]

else:

    exit("Error in filename..")


if len(open(script).readlines()) > 5:

    print("Script too long ! I'm lazy to cat all these lines..")

    exit(0)


# Simulate a real execution in terminal

screen = pyte.Screen(100, 10)

stream = pyte.Stream(screen)

stream.feed(execute('cat '+script))


for l in screen.display:

    line = l.rstrip()

    if len(line) >= 100:

        print("Print too long!")

        exit(0)


# Safe ?

safe = True

regex="(^print\([\"'][a-z A-Z]*[\"']\)[;]?$)|(^#.*)"


for l in screen.display:

    line = l.rstrip()

    if line != "" and not re.match(regex,line):

        safe = False

        print(" > " + line)


if safe:

    print("SAFE FILE EXECUTED: \n")

    print(execute("python3 "+script), end="")

else:

    print("Are you kidding ?! I'll only execute simple print !")

