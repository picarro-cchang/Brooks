import time

import click

import CmdFIFO

# Functions to make available for remote calls


class RpcServer:
    def __init__(self, port):
        self.rpc_server = CmdFIFO.CmdFIFOServer(("", port),
                                                ServerName="TestCmdFIFO",
                                                ServerDescription="Test server for CmdFIFO functionality",
                                                threaded=True)
        self.rpc_server.register_function(self.product)
        self.rpc_server.register_function(self.quotient)
        self.rpc_server.register_function(self.varsum)
        self.rpc_server.register_function(self.delay)

    def product(self, x, y):
        "Computes product of x and y"
        return x * y

    def quotient(self, x, y):
        "Computes quotient of x and y"
        return x / y

    def varsum(self, *a):
        "Computes sum of any number of arguments"
        return sum([x for x in a])

    def delay(self, x):
        "Delay by x seconds and return epoch time at completion"
        time.sleep(x)
        return time.time()


@click.command()
@click.option("--port", "-p", default=32769, help="Port for RPC server")
def main(port):
    try:
        server = RpcServer(port)
        print(f"RPC server started at port {port}.")
        server.rpc_server.serve_forever()
    finally:
        print(f"RPC server terminated.")

if __name__ == "__main__":
    main()
