import json
import socket


class NetworkModule:

    def get_ip_address(self, req):
        """
        Method use to get eth0 ip address and run modbus server using ip address for Modbus over TCPIP
        :return:
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            ip = {'ip':ip_address}
            # send response
            return json.dumps(ip), 200
        except Exception as ex:
            # if exception catch reply with error
            return json.dumps({"message": str(ex)}), 400
