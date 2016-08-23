# Client that doesn't use the Name Server. Uses URI directly.

import Pyro4
import sys
import threading
import time

def connectAndDelay(x):
    jokes = Pyro4.core.Proxy("PYRO:jokegen@localhost:7766")
    jokes.delay(x)

# you have to change the URI below to match your own host/port.
jokes = Pyro4.core.Proxy("PYRO:jokegen@localhost:7766")

start = time.time()
print "Start", start
threading.Thread(target=connectAndDelay, args=(0.2,)).start()
threading.Thread(target=connectAndDelay, args=(0.3,)).start()
threading.Thread(target=connectAndDelay, args=(0.2,)).start()
time.sleep(0.1)
print "Calling joke at", time.time()
jokes.joke("Irmen")
print "Joke completed at", time.time()
jokes.delay(0.3)
print "After final delay", time.time()