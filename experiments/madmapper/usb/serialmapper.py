import pyudev
import time
from host.experiments.common.serial_interface import SerialInterface
from host.experiments.common.rpc_ports import rpc_ports
from host.experiments.LOLogger.LOLoggerClient import LOLoggerClient


class SerialMapper(object):
    def __init__(self):
        self.devices = {"Serial_Devices": {}}
        self.relay_port = rpc_ports.get('relay_drivers')
        self.mfc_port = rpc_ports.get('mfc_drivers')
        self.piglet_port = rpc_ports.get('piglet_drivers')
        self.relay_count = 0
        self.mfc_count = 0
        self.piglet_count = 0
        self.logger = LOLoggerClient(client_name=__class__.__name__)

    def get_usb_serial_devices(self):
        self.relay_count = 0
        self.mfc_count = 0
        self.piglet_count = 0
        context = pyudev.Context()
        for device in context.list_devices(subsystem='tty', ID_BUS='usb'):
            self.logger.debug(f'Device found: {dict(device)}')
            if 'Numato' in device.get('ID_SERIAL'):
                serial_interface = SerialInterface()
                serial_interface.config(port=device.get('DEVNAME'),
                                        baudrate=19200)
                try:
                    serial_interface.open()
                    time.sleep(0.5)
                    serial_interface.write('id get\r')
                    time.sleep(0.25)
                    numato_id = int(
                        f'{serial_interface.read()}'.split('\n')[1][-1])
                    serial_interface.close()
                    relay_rpc_port = self.relay_port + numato_id
                    self.devices['Serial_Devices'].update({
                        f"{device.get('DEVNAME')}": {
                            'Driver': 'NumatoDriver',
                            'Path': device.get('DEVNAME'),
                            'Baudrate': 19200,
                            'Numato_ID': numato_id,
                            'RPC_Port': relay_rpc_port
                        }
                    })
                    self.relay_count += 1
                except Exception as e:
                    self.logger.critical(f'Unhandled Exception: {e}')
            elif 'Mega 2560 R3' in device.get('ID_MODEL_FROM_DATABASE'):
                serial_interface = SerialInterface()
                serial_interface.config(port=device.get('DEVNAME'),
                                        baudrate=38400)
                try:
                    serial_interface.open()
                    time.sleep(2)
                    serial_interface.write('slotid?\r')
                    time.sleep(0.25)
                    slot_id = int(f'{serial_interface.read()}'.rstrip('\n'))
                    serial_interface.close()
                    piglet_rpc_port = self.piglet_port + (slot_id - 1)
                    self.devices['Serial_Devices'].update({
                        f'{device.get("DEVNAME")}': {
                            'Driver': 'PigletDriver',
                            'Bank_ID': slot_id,
                            'Topaz_A_HW_Rev': 'Null',
                            'Topaz_B_HW_Rev': 'Null',
                            'Whitfield_HW_Rev': 'Null',
                            'Path': device.get('DEVNAME'),
                            'Baudrate': 38400,
                            'RPC_Port': piglet_rpc_port
                        }
                    })
                    self.piglet_count += 1
                except Exception as e:
                    self.logger.critical(f'Unhandled Exception: {e}')
            elif 'FTDI_FT232R_USB_UART_AL04J9KM' in device.get('ID_SERIAL'):
                mfc_rpc_port = self.mfc_port + self.mfc_count
                self.devices['Serial_Devices'].update({
                    f'{device.get("DEVNAME")}': {
                        'Driver': 'AlicatDriver',
                        'Path': device.get('DEVNAME'),
                        'Baudrate': 19200,
                        'RPC_Port': mfc_rpc_port
                    }
                })
                self.mfc_count += 1
        self.logger.debug(f'USB Serial Devices: {self.devices}')
        return self.devices


if __name__ == '__main__':
    from host.experiments.common.function_timer import FunctionTimer
    with FunctionTimer():
        print(f'SerialMapper Started...')
        test = SerialMapper()
        test.get_usb_serial_devices()
