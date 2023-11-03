#/usr/bin/env python3

from pyModbusTCP.client import ModbusClient

# Do zadawania jazdy wykorzystujemy rejestry D25032 i 25033. 
# Rejestr D25032 przyjmuje wartość 5 lub 6 lub 0 co oznacza kierunek jazdy. 
# 6 to jazda do przodu, 
# 5 to jazda do tyłu, 
# 0 to stop. 
# Rejestr D25033 przyjmuje wartość 0-4000  prędkość jazdy

Wozek_Stop = 0
Wozek_do_Tylu = 5 
Wozek_do_Przodu = 6 

Servo_Off = 0 
Servo_Zeroj  = 3
Servo_Obrot =  5

# deltaPLC = ModbusClient(host='192.168.1.4', port=502, auto_open=True)

def MoveStearingWheel(angle_impulses, action_type):
    try:
        # if action_type != (Servo_Off, Servo_Zeroj, Servo_Obrot):
        #     action_type = Servo_Off
        #     deltaPLC.write_single_register(25041, Servo_Off)
        #     exit()            

        if action_type == Servo_Off:
            deltaPLC.write_single_register(25041, Servo_Off)

        elif action_type == Servo_Zeroj:
            deltaPLC.write_single_register(25041, 15)
            deltaPLC.write_single_register(25042, 1)
            deltaPLC.write_single_register(25042, 3)

        elif action_type == Servo_Obrot:
            if angle_impulses < 0:
                deltaPLC.write_single_register(25044, -1)
                deltaPLC.write_single_register(25043, angle_impulses)
            else:
                deltaPLC.write_single_register(25044, 0)
                deltaPLC.write_single_register(25043, angle_impulses)
            deltaPLC.write_single_register(25041, 15)
            deltaPLC.write_single_register(25042, 1)
            deltaPLC.write_single_register(25042, 5)

    except:
        print("Error")


if __name__ == '__main__':
    try:
        deltaPLC = ModbusClient(host='192.168.1.4', port=502, auto_open=True)
        MoveStearingWheel(-5000, Servo_Off)
    except:
        pass