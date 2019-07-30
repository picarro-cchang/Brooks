from aiomultiprocess import Process
import asyncio
import traceback
import CmdFIFO
import Pyro4
from RpcServer import RpcServer

PORT = 32769
Remote = CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{PORT}", "test")

process_list = []

class AsyncWrapper:
    """Returns asynchronous version of a method by wrapping it in an executor"""
    def __init__(self, proxy):
        self.proxy = proxy

    def __getattr__(self, attr):
        return AsyncWrapper(getattr(self.proxy, attr))
    
    async def __call__(self, *args, **kwargs):
        return await asyncio.get_running_loop().run_in_executor(None, self.proxy, *args, **kwargs)


async def dotty():
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.5)

async def process_monitor():
    while True:
        for p in process_list:
            print(f"{dir(p)} {p.name} {p.pid} {p.is_alive()} {p.exitcode}")
        print(80*'-')
        await asyncio.sleep(1.0)

async def pinger(p, server_proxy):
    try:
        while True:
            if await asyncio.wait_for(server_proxy.ping(), timeout=6) == 'OK':
                print("+", end="", flush=True)
            await asyncio.sleep(2.0)
    except CmdFIFO.RemoteException:
        print("Ping exception")
        p.kill()
    except asyncio.TimeoutError:
        print("Ping timeout")
        p.kill()

async def start_server():
    port = PORT
    server = RpcServer(port)
    print(f"RPC server started at port {port}.")
    return server.rpc_server.serve_forever()

async def main():
    # asyncio.create_task(process_monitor())
    while True:
        print("Restarting RPC server")
        p = Process(target=start_server)
        p.daemon = True
        p.metadata = "My metadata"
        process_list.append(p)
        p.start()
        ARemote = AsyncWrapper(Remote)
        asyncio.create_task(pinger(p, ARemote))
        try:
            while True:
                print(f"\nResult of delay {await ARemote.delay(1)}")
                print(f"\nResult of product {await ARemote.product(5, 6)}")
                print(f"\nMethod signature {await ARemote.system.methodSignature('product')}")
                print(f"\nResult of quotient {await ARemote.quotient(15, 7)}")
        except CmdFIFO.RemoteException:
            print(f"RPC remote exception: {traceback.format_exc()}")
        finally:
            await p.join()

if __name__ == "__main__":
    asyncio.run(main())
