import CmdFIFO
import time

# TODO
#   Remove local import
#   Remove hard coded host
#   Remove hard coded port
TestClient = CmdFIFO.CmdFIFOServerProxy("http://10.100.3.95:6667",
                                    "test", IsDontCareConnection=False)


print(TestClient.CmdFIFO.PingFIFO())
print(TestClient.CmdFIFO.GetProcessID())

methods = TestClient.system.listMethods()
for method in methods:
    print(method + " " + TestClient.system.methodSignature(method))


def get_flow_delta():
    while True:
        print(f'Delta Flow: {TestClient.get_flow_delta()}')
        time.sleep(0.5)


def set_flow_setpoint(setpoint):
    TestClient.set_set_point(setpoint)


def get_flow_setpoint():
    flow_setpoint = TestClient.get_set_point()
    return flow_setpoint


def get_data():
    data = TestClient.get_data()
    return data


def get_data_dict():
    data_dict = TestClient.get_data_dict()
    return data_dict


if __name__ == '__main__':
    print('\n')
    print(f'Current Setpoint: {get_flow_setpoint()}')
    setpoint = input('Enter new MFC setpoint in SLPM: ')
    print('Starting AlicatDriver TestClient')
    print(f'Setting MFC Setpoint to {setpoint}')
    set_flow_setpoint(setpoint)
    time.sleep(0.5)
    print(f'Current Setpoint: {get_flow_setpoint()}')
    print('\n')
    while True:
        print(get_data_dict())
        time.sleep(0.2)


