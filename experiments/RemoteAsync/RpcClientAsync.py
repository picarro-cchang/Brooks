import asyncio
import traceback
import CmdFIFO

PORT = 32769
Remote = CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{PORT}", "test")


class AsyncWrapper:
    def __init__(self, proxy):
        self.proxy = proxy

    def __getattr__(self, attr):
        """Returns asynchronous version of a method by wrapping it in an executor"""

        async def func(*args, **kwargs):
            return await asyncio.get_running_loop().run_in_executor(None, getattr(self.proxy, attr), *args, **kwargs)
        return func

async def dotty():
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.5)


async def main():
    asyncio.create_task(dotty())
    ARemote = AsyncWrapper(Remote)

    print(f"\nResult of delay {await ARemote.delay(5)}")
    print(f"\nResult of product {await ARemote.product(5, 6)}")
    print(f"\nResult of quotient {await ARemote.quotient(5, 0)}")

if __name__ == "__main__":
    asyncio.run(main())
