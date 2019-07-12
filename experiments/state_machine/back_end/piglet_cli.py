"""
The piglet_cli utility allows interaction with the piglet simulator
"""
import asyncio
import os
import attr

from piglet_simulator import PigletSimulator

# Windows
if os.name == 'nt':
    import msvcrt

# Posix (Linux, OS X)
else:
    import sys
    import termios
    import atexit
    from select import select


class KBHit:
    def __init__(self):
        '''Creates a KBHit object that you can call to do various keyboard things.
        '''

        if os.name == 'nt':
            pass

        else:

            # Save the terminal settings
            self.fd = sys.stdin.fileno()
            self.new_term = termios.tcgetattr(self.fd)
            self.old_term = termios.tcgetattr(self.fd)

            # New terminal setting unbuffered
            self.new_term[3] = (self.new_term[3] & ~termios.ICANON & ~termios.ECHO)
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.new_term)

            # Support normal-terminal reset at exit
            atexit.register(self.set_normal_term)

    def set_normal_term(self):
        ''' Resets to normal terminal.  On Windows this is a no-op.
        '''

        if os.name == 'nt':
            pass

        else:
            termios.tcsetattr(self.fd, termios.TCSAFLUSH, self.old_term)

    def getch(self):
        ''' Returns a keyboard character after kbhit() has been called.
            Should not be called in the same program as getarrow().
        '''
        if os.name == 'nt':
            return msvcrt.getch().decode('utf-8')

        else:
            return sys.stdin.read(1)

    def getarrow(self):
        ''' Returns an arrow-key code after kbhit() has been called. Codes are
        0 : up
        1 : right
        2 : down
        3 : left
        Should not be called in the same program as getch().
        '''

        if os.name == 'nt':
            msvcrt.getch()  # skip 0xE0
            c = msvcrt.getch()
            vals = [72, 77, 80, 75]

        else:
            c = sys.stdin.read(3)[2]
            vals = [65, 67, 66, 68]

        return vals.index(ord(c.decode('utf-8')))

    def kbhit(self):
        ''' Returns True if keyboard character was hit, False otherwise.
        '''
        if os.name == 'nt':
            return msvcrt.kbhit()

        else:
            dr, dw, de = select([sys.stdin], [], [], 0)
            return dr != []


# We need to poll each piglet periodically for a collection of status data
# 1. The piglet state: one of power_up, standby, ident, sampling, clean, reference, fault, power_off
# 2. The MFC setting
# 3. The solenoid valve setting (8 bits, one per channel)
# 4. The bypass (proportional) valves (8 integers, one per channel)
# 5. The flow rates (8 floats, one per channel)
# 6. An error code


@attr.s
class PigletCli:
    piglet = attr.ib(factory=lambda: PigletSimulator(bank=1))

    async def main(self):
        kb = KBHit()
        while True:
            print(">> ", end="", flush=True)
            command = ""
            while True:
                try:
                    if kb.kbhit():
                        c = kb.getch()
                        if c != "\r":
                            print(c, end="", flush=True)
                            command += c
                        else:
                            print()
                            print(await self.piglet.cli(command))
                            break
                except:
                    pass
                await asyncio.sleep(0.01)


async def main():
    pm = PigletCli()
    await asyncio.gather(pm.main(), pm.piglet.fsm())


if __name__ == "__main__":
    asyncio.run(main())
