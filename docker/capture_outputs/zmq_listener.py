import zmq

PORT = 40000

def main():
    """ main method """

    # Prepare our context and publisher
    context    = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.connect("tcp://localhost:%d" % (PORT,))
    subscriber.setsockopt(zmq.SUBSCRIBE, "")

    while True:
        # Read envelope with address
        print subscriber.recv_string()

    # We never get here but clean up anyhow
    subscriber.close()
    context.term()

if __name__ == "__main__":
    main()
