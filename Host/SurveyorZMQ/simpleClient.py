import zmq
from Host.Common.SharedTypes import ZMQ_PORT_SURVEYOR_CMD

context = zmq.Context()
requester = context.socket(zmq.REQ)
requester.connect("tcp://localhost:%d" % ZMQ_PORT_SURVEYOR_CMD)

commands = ["Shutdown", "StartReferenceGasCapture", 
            "StartIsotopicCapture", "CancelCapture", 
            "StartReferenceGasInjection"]

while True:
    print "Select command:"
    for i, c in enumerate(commands):
        print "%d: %s" % (i, c)
    try:
        cmd = commands[int(raw_input())]
    except:
        print "Invalid input"
        continue
    requester.send(cmd)
    print requester.recv()
