import socket
import subprocess
from common import CmdFIFO
from common.rpc_ports import rpc_ports
from back_end.lologger.lologger_client import LOLoggerClient


class NetworkMapper(object):
    def __init__(self):
        self.picarro_hosts = {"Network_Devices": {}}
        self.network_prefix = '192.168.10.'
        self.host_port = 50010
        self.instrument_rpc_port = rpc_ports.get('instrument_drivers')
        self.logger = LOLoggerClient(client_name=__class__.__name__)

    @staticmethod
    def get_ip_addresses():
        ip_addresses = subprocess.getoutput('hostname -I')
        ip_list = ip_addresses.split()
        return ip_list

    def get_rack_lan_ip(self, ip_addresses):
        ip = None
        for ip in range(0, len(ip_addresses)):
            if self.network_prefix in ip_addresses[ip]:
                ip = ip_addresses[ip]
                break
        return ip

    def is_picarro_host(self, host, port=50010, timeout=0.1):
        s = socket.socket()
        s.settimeout(timeout)
        result = False
        try:
            s.connect((host, port))
            s.close()
            result = True
        except socket.error as e:
            self.logger.warning(f'Socket Exception: {e}')
        finally:
            self.logger.debug(f'{host} is Picarro Instrument: {result}')
        return result

    @staticmethod
    def ping_host(host):
        ping = subprocess.Popen(['ping', '-c', '1', '-W', '1', f'{host}'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        ping.communicate()
        return_code = ping.returncode
        if return_code == 0:
            return True
        else:
            return False

    def get_all_active_hosts(self):
        current = start = 2
        end = 255
        hosts = []
        ip_addresses = [
            subprocess.Popen(['ping', '-c', '1', '-W', '1', f'{self.network_prefix}{x}'],
                             stderr=subprocess.PIPE,
                             stdout=subprocess.PIPE) for x in range(start, end)
        ]
        for ip in ip_addresses:
            ip.communicate()
            return_code = ip.returncode
            if return_code == 0:
                hosts.append(f'{self.network_prefix}{current}')
            current += 1
        self.logger.debug(f'Active hosts: {hosts}'
                          f'\nTotal hosts up: {len(hosts)}'
                          f'\nHosts scanned: {end - start} '
                          f'({self.network_prefix}{start} - '
                          f'{self.network_prefix}{end})\n')
        return hosts

    def get_all_picarro_hosts(self):
        instrument_count = 0
        active_hosts = self.get_all_active_hosts()
        rack_ip = self.get_rack_lan_ip(self.get_ip_addresses())
        if rack_ip in active_hosts:
            active_hosts.remove(rack_ip)
        for ip_address in active_hosts:
            if self.is_picarro_host(ip_address) is True:
                try:
                    driver = CmdFIFO.CmdFIFOServerProxy(f'http://{ip_address}:{self.host_port}', ClientName='NetworkMapper')
                    instrument_dict = driver.fetchLogicEEPROM()[0]
                    serial_number = f'{instrument_dict.get("Chassis")}-' \
                        f'{instrument_dict.get("Analyzer")}' \
                        f'{instrument_dict.get("AnalyzerNum")}'
                    if serial_number not in self.picarro_hosts['Network_Devices']:
                        rpc_port = self.instrument_rpc_port + instrument_count
                        self.picarro_hosts['Network_Devices'].update({
                            f'{serial_number}': {
                                'IP': f'{ip_address}',
                                'SN': serial_number,
                                'Driver': 'IDriver',
                                'RPC_Port': rpc_port
                            }
                        })
                        instrument_count += 1
                except Exception as e:
                    self.logger.error(f'Unhandled Exception: {e}')
        self.logger.debug(f'Picarro hosts: {self.picarro_hosts}\n')
        return self.picarro_hosts


if __name__ == '__main__':
    from common.function_timer import FunctionTimer
    with FunctionTimer(time_unit='s'):
        test = NetworkMapper()
        test.get_all_picarro_hosts()
