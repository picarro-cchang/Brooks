import asyncio
from aiomultiprocess import Process
import CmdFIFO
from experiments.common.rpc_ports import rpc_ports
from experiments.madmapper.madmapper import MadMapper

host = "10.100.3.28"
port = rpc_ports.get('madmapper')


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


async def start_madmapper():
    MadMapper()


async def main():
    asyncio.create_task(dotty())
    process_list = []
    p = Process(target=start_madmapper)
    p.daemon = True
    p.metadata = "My metadata"
    process_list.append(p)
    p.start()
    AMadMapper = AsyncWrapper(CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{rpc_ports.get('madmapper')}", "supervisor"))
    print(f"\nResult of MadMapper.read_json {await AMadMapper.read_json()}")
    device_dict = await AMadMapper.map_devices(False)
    print(f"\nResult of MadMapper.map_devices {device_dict}")


if __name__ == "__main__":
    asyncio.run(main())
