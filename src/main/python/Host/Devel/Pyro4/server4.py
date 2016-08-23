# The server that doesn't use the Name Server.

import os
import Pyro4
import time

class JokeGen(object):
    def joke(self, name):
        print "joke starts at ", time.time()
        return "Sorry "+name+", I don't know any jokes."
    def delay(self, sec):
        print "delay starts at ", time.time()
        time.sleep(sec)

def main():
    servertype = "t"
    if servertype=="t":
        Pyro4.config.SERVERTYPE="thread"
    else:
        Pyro4.config.SERVERTYPE="multiplex"
    daemon = Pyro4.core.Daemon(port=7766)    
    uri1=daemon.register(JokeGen(), objectId="jokegen")   # let Pyro create a unique name for this one
    
    print("JokeGen is ready, not using the Name Server.")
    print(uri1)
    daemon.requestLoop()

if __name__=="__main__":
    main()
