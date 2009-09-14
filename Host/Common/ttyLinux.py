#@+leo-ver=4-thin
#@+node:root.20080402111310.37:@thin Common/ttyLinux.py
#!/usr/local/bin/python
#
# ttyLinux.py
#
# readLookAhead reads lookahead chars from the keyboard without
# echoing them. It still honors ^C etc
#
import termios, sys, time

def setSpecial () :
    "set keyboard to read single chars lookahead only"
    global oldTermiosSettings
    fd = sys.stdin.fileno()
    oldTermiosSettings = termios.tcgetattr(fd)
    new = termios.tcgetattr(fd)
    new[3] = new[3] & ~termios.ECHO # lflags
    new[3] = new[3] & ~termios.ICANON # lflags
    new[6][6] = '\000' # Set VMIN to zero for lookahead only
    termios.tcsetattr(fd, termios.TCSADRAIN, new)

def setNormal () :
    "restore previous keyboard settings"
    global oldTermiosSettings
    fd = sys.stdin.fileno()
    termios.tcsetattr(fd, termios.TCSADRAIN, oldTermiosSettings)

def readLookAhead () :
    "read max 1 chars (arrow escape seq) from look ahead"
    return sys.stdin.read(1)

if __name__ == "__main__":
	setSpecial()
	for i in range(10) :
		time.sleep(1)
		keys = readLookAhead()
		print "Got", [keys]
	setNormal()
#@-node:root.20080402111310.37:@thin Common/ttyLinux.py
#@-leo
