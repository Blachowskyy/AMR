from multiprocessing.connection import wait
from easymodbus import modbusClient

class Main:
    encoder = modbusClient.ModbusClient('192.168.1.20', 502)
    encoder.connect()
    wait(10)
    if encoder.is_connected:
        try:
            print('polaczylem')
        except:
            print('problem')

        



