from pyModbusTCP.client import ModbusClient
c=ModbusClient(host='localhost',port=9999,auto_open=True)

regs=c.read_holding_registers(403705,1)
print("Reading register values")

if regs:
   print(regs)
else:
   print("error")

print("write value to register")
a=int(input())
c.write_single_register(403705,a)
