import socket
import subprocess
import CmdFIFO
from conf import network_prefix, host_port


class NetworkMapper(object):

    @staticmethod
    def get_ip_addresses():
        ip_addresses = subprocess.getoutput('hostname -I')
        ip_list = ip_addresses.split()
        return ip_list

    def get_rack_lan_ip(self, ip_addresses):
        ip = None
        for ip in range(0, len(ip_addresses)):
            if network_prefix in ip_addresses[ip]:
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
            if __debug__:
                print(f'Socket Exception: {e}')
        finally:
            if __debug__:
                print(f'{host} is Picarro Instrument: {result}')
        return result

    def ping_host(self, host):
        ping = subprocess.Popen(['ping', '-c', '1', '-W', '1', f'{host}'],
                                stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE)
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
        ip_addresses = [subprocess.Popen(
            ['ping', '-c', '1', '-W', '1', f'{network_prefix}{x}'],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE) for x in range(start, end)]
        for ip in ip_addresses:
            ip.communicate()
            return_code = ip.returncode
            if return_code == 0:
                hosts.append(f'{network_prefix}{current}')
            current += 1
        if __debug__:
            print(f'\nActive hosts: {hosts}'
                  f'Total hosts up: {len(hosts)}'
                  f'Hosts scanned: {end - start}\n')
        return hosts

    def get_all_picarro_hosts(self):
        picarro_hosts = {}
        active_hosts = self.get_all_active_hosts()
        rack_ip = self.get_rack_lan_ip(self.get_ip_addresses())
        if rack_ip in active_hosts:
            active_hosts.remove(rack_ip)
        for ip_address in active_hosts:
            if self.is_picarro_host(ip_address) is True:
                driver = CmdFIFO.CmdFIFOServerProxy(
                    f'http://{ip_address}:{host_port}',
                    ClientName='NetworkMapper')
            try:
                instrument_dict = driver.fetchLogicEEPROM()[0]
                serial_number = f'{instrument_dict.get("Chassis")}-' \
                    f'{instrument_dict.get("Analyzer")}' \
                    f'{instrument_dict.get("AnalyzerNum")}'
                if not picarro_hosts.get(serial_number):
                    picarro_hosts.update({f'{serial_number}': f'{ip_address}'})
            except Exception as e:
                print(e)
        if __debug__:
            print(f'Picarro hosts: {picarro_hosts}\n')
        return picarro_hosts


if __name__ == '__main__':
    from host.experiments.common.function_timer import FunctionTimer
    with FunctionTimer(time_unit='s'):
        test = NetworkMapper()
        test.get_all_picarro_hosts()
