import time

import pyudev
from back_end.lologger.lologger_client import LOLoggerClient
from common.rpc_ports import rpc_ports
from common.serial_interface import SerialInterface
from back_end.relay_driver.numato.numato_driver import UsbRelay


class SerialMapper(object):
    def __init__(self):
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
        devices = {"Serial_Devices": {}}
        for device in context.list_devices(subsystem='tty', ID_BUS='usb'):
            self.logger.debug(f'Device found: {dict(device)}')
            if 'Numato' in device.get('ID_SERIAL'):
                port = device.get('DEVNAME')
                try:
                    usb_relay = UsbRelay(port_name=port, logger=self.logger)
                    # Fix for PIG-467
                    # Numato sends garbage data on first query after initial power-on
                    usb_relay.send_garbage("garbage")
                    numato_id = int(usb_relay.get_id())
                    usb_relay.serial_port.close()
                    relay_rpc_port = self.relay_port + int(numato_id)
                    devices['Serial_Devices'].update({
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
                    self.logger.error(f'Unhandled Exception: {e}')
            elif device.get('ID_SERIAL').startswith('Picarro_Piglet'):
                serial_interface = SerialInterface()
                serial_interface.config(port=device.get('DEVNAME'), baudrate=230400)
                try:
                    serial_interface.open()
                    time.sleep(2.0)
                    # Get slot id of sample module
                    serial_interface.write('slotid?\r')
                    slot_id = int(serial_interface.read().strip())
                    # Get serial number of Topaz A board
                    serial_interface.write('tza.sn?\r')
                    topaz_a_sn = serial_interface.read().strip()
                    # get serial number of Topaz B board
                    serial_interface.write('tzb.sn?\r')
                    topaz_b_sn = serial_interface.read().strip()
                    # get manifold firmware version
                    serial_interface.write('*idn?\r')
                    # Response string example:
                    #     Picarro,Boxer,SN65000,1.1.5
                    fw_ver = serial_interface.read().split(',')[-1]
                    serial_interface.close()
                    piglet_rpc_port = self.piglet_port + (slot_id - 1)
                    devices['Serial_Devices'].update({
                        f'{device.get("DEVNAME")}': {
                            'Driver': 'PigletDriver',
                            'Slot_ID': slot_id,
                            'Topaz_A_SN': topaz_a_sn,
                            'Topaz_B_SN': topaz_b_sn,
                            'Manifold_SN': device.get('ID_SERIAL_SHORT'),
                            'Manifold_FW': fw_ver.strip(),
                            'Path': device.get('DEVNAME'),
                            'Baudrate': 230400,
                            'RPC_Port': piglet_rpc_port
                        }
                    })
                    self.piglet_count += 1
                except Exception as e:
                    self.logger.error(f'Unhandled Exception: {e}')
            elif 'FTDI_FT232R_USB_UART_' in device.get('ID_SERIAL') or "FTDI_USB-RS232_Cable_" in device.get('ID_SERIAL'):
                mfc_rpc_port = self.mfc_port + self.mfc_count
                devices['Serial_Devices'].update({
                    f'{device.get("DEVNAME")}': {
                        'Driver': 'AlicatDriver',
                        'Path': device.get('DEVNAME'),
                        'Baudrate': 19200,
                        'RPC_Port': mfc_rpc_port
                    }
                })
                self.mfc_count += 1
        self.logger.debug(f'USB Serial Devices: {devices}')
        return devices


if __name__ == '__main__':
    from common.function_timer import FunctionTimer
    with FunctionTimer():
        print(f'SerialMapper Started...')
        test = SerialMapper()
        test.get_usb_serial_devices()
