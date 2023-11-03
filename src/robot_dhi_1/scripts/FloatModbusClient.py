#!/usr/bin/env python3

from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import encode_ieee, decode_ieee, long_list_to_word, word_list_to_long

class FloatModbusClient(ModbusClient):

    def read_float(self, address, number=1):
        address = (address * 4) + 1
        data_1 = self.read_holding_registers(address, number * 2)
        if data_1:
            return [decode_ieee(f) for f in word_list_to_long(data_1)]
        else:
            return None
    def write_float(self, address, float_list):
        address = (address * 4) + 1
        data_1 = [encode_ieee(f) for f in float_list]
        data_1_encoded = long_list_to_word(data_1, big_endian=True)
        return self.write_multiple_registers(address, data_1_encoded)
    

if __name__ == '__main__':
    deltaPLC = FloatModbusClient(host='192.168.1.4', port=502, auto_open=True, auto_close=True)
    # while True:

    deltaPLC.write_float(0, [-12.15])
    print('done')
    test = deltaPLC.read_float(0, 1)
    print(f"Odczyt: {test[0]}")