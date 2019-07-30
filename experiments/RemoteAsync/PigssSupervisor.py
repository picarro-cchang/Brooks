import asyncio
import attr
from aiomultiprocess import Process
import CmdFIFO
from collections import defaultdict
from experiments.common.rpc_ports import rpc_ports
from experiments.madmapper.madmapper import MadMapper
from experiments.piglet.piglet_driver import PigletDriver
from experiments.relay_driver.numato_driver_proto import NumatoDriver
from experiments.mfc_driver.alicat.alicat_driver import AlicatDriver

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

@attr.s
class ProcessWrapper:
    driver = attr.ib()
    rpc_port = attr.ib(type=int)
    process = attr.ib(None, type=Process)
    rpc_wrapper = attr.ib(None)

    async def start(self, *args, **kwargs):
        async def start_driver():
            d = self.driver(*args, **kwargs)
            d.rpc_serve_forever()
        if self.process is not None and self.process.is_alive():
            self.process.kill()
            await self.process.join()
        self.process = Process(target=start_driver)
        self.process.daemon = True
        self.process.start()
        self.rpc_wrapper = AsyncWrapper(CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{self.rpc_port}", "PigssSupervisor"))
        await asyncio.sleep(0.1)
        return self.rpc_wrapper

    async def pinger(self, period):
        try:
            while True:
                await asyncio.sleep(period)
                if await asyncio.wait_for(self.rpc_wrapper.CmdFIFO.PingFIFO(), timeout=2*period) == 'Ping OK':
                    print("+", end="", flush=True)
        except CmdFIFO.RemoteException:
            print("Ping caused exception")
            self.process.kill()
        except asyncio.TimeoutError:
            print("Ping timeout")
            self.process.kill()



async def dotty():
    while True:
        print(".", end="", flush=True)
        await asyncio.sleep(0.5)


class PigssSupervisor:
    def __init__(self):
        self.process_wrappers = {}  # List of Process objects
        self.RPC = {}  # Asynchronous interface to RPC handlers of spervisees
        self.device_dict = {}

    async def error_recovery(self, period):
        relay_id = 0
        while True:
            await asyncio.sleep(period)
            if not self.process_wrappers["MadMapper"].process.is_alive():
                print(f"Restarting MadMapper")
                process_wrapper = ProcessWrapper(MadMapper, rpc_ports.get('madmapper'))
                self.process_wrappers["MadMapper"] = process_wrapper
                self.RPC["MadMapper"] = await process_wrapper.start()

            for key, dev_params in sorted(self.device_dict['Devices']['Serial_Devices'].items()):
                if dev_params['Driver'] == 'PigletDriver':
                    if not self.process_wrappers[key].process.is_alive():
                        print(f"Restarting {key}")
                        process_wrapper = ProcessWrapper(PigletDriver, dev_params['RPC_Port'])
                        self.process_wrappers[key] = process_wrapper
                        self.RPC[f"Piglet_{dev_params['Bank_ID']}"] = await process_wrapper.start(
                            port=dev_params['Path'], rpc_port=dev_params['RPC_Port'], baudrate=dev_params['Baudrate']
                        )
                elif dev_params['Driver'] == 'AlicatDriver':
                    if not self.process_wrappers[key].process.is_alive():
                        print(f"Restarting {key}")
                        process_wrapper = ProcessWrapper(AlicatDriver, dev_params['RPC_Port'])
                        self.process_wrappers[key] = process_wrapper
                        self.RPC["MFC"] = await process_wrapper.start(
                            port=dev_params['Path'], rpc_port=dev_params['RPC_Port'], baudrate=dev_params['Baudrate']
                        )
                elif dev_params['Driver'] == 'NumatoDriver':
                    if not self.process_wrappers[key].process.is_alive():
                        print(f"Restarting {key}")
                        process_wrapper = ProcessWrapper(NumatoDriver, dev_params['RPC_Port'])
                        self.process_wrappers[key] = process_wrapper
                        relay_id += 1
                        self.RPC[f"Relay_{relay_id}"] = await process_wrapper.start(
                            device_port_name=dev_params['Path'], rpc_server_port=dev_params['RPC_Port']
                        )


    async def main(self):
        process_wrapper = ProcessWrapper(MadMapper, rpc_ports.get('madmapper'))
        self.process_wrappers["MadMapper"] = process_wrapper
        asyncio.create_task(process_wrapper.pinger(5))
        self.RPC["MadMapper"] = await process_wrapper.start()
        self.device_dict = await self.RPC["MadMapper"].read_json()
        print(f"\nResult of MadMapper.read_json {self.device_dict}")
        relay_id = 0
        for key, dev_params in sorted(self.device_dict['Devices']['Serial_Devices'].items()):
            if dev_params['Driver'] == 'PigletDriver':
                process_wrapper = ProcessWrapper(PigletDriver, dev_params['RPC_Port'])
                self.process_wrappers[key] = process_wrapper
                self.RPC[f"Piglet_{dev_params['Bank_ID']}"] = await process_wrapper.start(
                    port=dev_params['Path'], rpc_port=dev_params['RPC_Port'], baudrate=dev_params['Baudrate']
                )
            elif dev_params['Driver'] == 'AlicatDriver':
                process_wrapper = ProcessWrapper(AlicatDriver, dev_params['RPC_Port'])
                self.process_wrappers[key] = process_wrapper
                self.RPC["MFC"] = await process_wrapper.start(
                    port=dev_params['Path'], rpc_port=dev_params['RPC_Port'], baudrate=dev_params['Baudrate']
                )
            elif dev_params['Driver'] == 'NumatoDriver':
                process_wrapper = ProcessWrapper(NumatoDriver, dev_params['RPC_Port'])
                self.process_wrappers[key] = process_wrapper
                relay_id += 1
                self.RPC[f"Relay_{relay_id}"] = await process_wrapper.start(
                    device_port_name=dev_params['Path'], rpc_server_port=dev_params['RPC_Port']
                )
            asyncio.create_task(process_wrapper.pinger(2))

        await self.error_recovery(5.0)

if __name__ == "__main__":
    ps = PigssSupervisor()
    asyncio.run(ps.main())
