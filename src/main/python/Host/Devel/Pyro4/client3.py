import Pyro.core
import threading
import time

# you have to change the URI below to match your own host/port.
jokes = Pyro.core.getProxyForURI("PYROLOC://localhost:7766/jokegen")

start = time.time()
print "Start", start
threading.Thread(target=lambda x:jokes.delay(x), args=(0.2,)).start()
threading.Thread(target=lambda x:jokes.delay(x), args=(0.3,)).start()
threading.Thread(target=lambda x:jokes.delay(x), args=(0.2,)).start()
time.sleep(0.1)
print "Calling joke at", time.time()
jokes.joke("Irmen")
print "Joke completed at", time.time()
jokes.delay(0.3)
print "After final delay", time.time()
