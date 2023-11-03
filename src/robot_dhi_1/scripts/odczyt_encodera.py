#!/usr/bin/env python3

import os
import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import  Float32, Bool
#Deklaracje zmiennych
speed = 0
speed_conv = 0
direction = 0
in_motion = False
encoder_status = True

#deklaracja publikowanego topicu oraz polaczenia
pub = rospy.Publisher('wozek_speed', Float32, queue_size=1)
in_motion_pub = rospy.Publisher('motion_status', Bool, queue_size =1)
rospy.init_node('encoder', anonymous=True)
encoder_status_pub = rospy.Publisher('encoder/status', Bool, queue_size=1)
rate = rospy.Rate(10) # 1hz
c=ModbusClient(host='192.168.1.4',port=502,auto_open=True)

#velocity and direction - adress (206, 2)
#1 rejestr - predkosc
#2 rejest - kierunek
def publisher():
    
    rospy.loginfo("Encoder read started")
    while not rospy.is_shutdown():
        #Odczyt dwoch rejestrow z sterownika PLC
        odczyt = c.read_holding_registers(206, 2)
        #Rozbicie odczytanej tablicy na pojedyncze zmienne
        direction = odczyt[1]
        speed = odczyt[0]
        #W zaleznosci od kierunku ustanowienie znaku przed wartoscia predkosci
        if direction == 1:
            speed = speed
        elif direction == 2:
            speed = -speed
        #W przypadku otrzymania niezgodnej liczby - innej ni 1 lub 2 ( kierunek ) - blad
        else :
            speed = 0
            direction = 0
            rospy.loginfo("Error in direction reading from PLC")
            encoder_status = False
        #Dzielenie przez 100 w celu uzyskania dokadnosci 0,01 - brak mozliwosci odczytu
        #liczby zmiennoprzecinkowej
        speed_conv = speed / 100
        if speed != 0 :
            in_motion = True
        if speed == 0 :
            in_motion = False

        #Wypisanie predkosci i kierunku w konsoli
        diag_comunicate = f"\nPredkosc: {speed_conv} \nKierunek: {direction}"
        rospy.loginfo(diag_comunicate)
        #Publikacja wartosci predkosci do topicu
        pub.publish(speed_conv)
        in_motion_pub.publish(in_motion)
        rate.sleep()
        clear = lambda: os.system('clear')
        clear()

if __name__ == '__main__':
    try:
        publisher()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)
    finally:
        rospy.loginfo('exit')
