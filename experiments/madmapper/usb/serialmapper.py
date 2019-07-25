import pyudev
import time
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.common.rpc_ports import rpc_ports

class SerialMapper(object):
    def __init__(self):
        self.devices = {"Serial_Devices": {}}
        self.relay_port = rpc_ports.get('relay_drivers')
        self.mfc_port = rpc_ports.get('mfc_drivers')
        self.piglet_port = rpc_ports.get('piglet_drivers')
        self.relay_count = 0
        self.mfc_count = 0
        self.piglet_count = 0

    def get_usb_serial_devices(self):
        context = pyudev.Context()
        for device in context.list_devices(subsystem='tty',
                                           ID_BUS='usb'):
            if __debug__:
                from pprint import pprint
                pprint(f'\n\n{dict(device)}\n\n')
            if 'Numato' in device.get('ID_SERIAL'):
                self.devices['Serial_Devices'].update({
                    f"{device.get('DEVNAME')}": {'Driver': 'NumatoDriver',
                                                 'Path': device.get('DEVNAME'),
                                                 'Baudrate': 19200,
                                                 'RPC_Port': self.relay_port + self.relay_count}})
                self.relay_count += 1
            elif 'Mega 2560 R3' in device.get('ID_MODEL_FROM_DATABASE'):
                serial_interface = SerialInterface()
                serial_interface.config(
                    port=device.get('DEVNAME'),
                    baudrate=38400
                )
                try:
                    serial_interface.open()
                    time.sleep(2)
                    serial_interface.write('slotid?\r')
                    time.sleep(0.25)
                    slot_id = f'{serial_interface.read()}'.rstrip('\n')
                    serial_interface.close()
                except Exception as e:
                    print(f'\n\n\nException: {e}\n\n\n')
                    slot_id = -1
                self.devices['Serial_Devices'].update({
                    f'{device.get("DEVNAME")}': {'Driver': 'PigletDriver',
                                                 'Bank_ID': int(slot_id),
                                                 'Path': device.get('DEVNAME'),
                                                 'Baudrate': 38400,
                                                 'RPC_Port': self.piglet_port + self.piglet_count}})
                self.piglet_count += 1
            elif 'FTDI_FT232R_USB_UART_AL04J9KM' in device.get('ID_SERIAL'):
                self.devices['Serial_Devices'].update({
                    f'{device.get("DEVNAME")}': {'Driver': 'AlicatDriver',
                                                 'Path': device.get('DEVNAME'),
                                                 'Baudrate': 19200,
                                                 'RPC_Port': self.mfc_port + self.mfc_count}})
                self.mfc_count += 1
        if __debug__:
            import json
            print(json.dumps(self.devices))
        return self.devices


if __name__ == '__main__':
    from host.experiments.common.function_timer import FunctionTimer
    with FunctionTimer():
        test = SerialMapper()
        test.get_usb_serial_devices()
