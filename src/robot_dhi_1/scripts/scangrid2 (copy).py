#!/usr/bin/env python3
import os
import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import Int64, Bool, Int64MultiArray

def publisher():

    #Deklaracja topic list wysylanych do ROS
    scangrid2_pub1 = rospy.Publisher('scangrid_1', Int64MultiArray, queue_size=10)
    scangrid2_pub2 = rospy.Publisher('scangrid_2', Int64MultiArray, queue_size=10)
    rospy.init_node('publisher', anonymous=True)

    #Deklaracja polaczenia modbus
    delta = ModbusClient(host='192.168.1.5',port=502,auto_open=True, auto_close=True)
    rate = rospy.Rate(30) # 1hz
    rospy.loginfo("Publisher high started")
    scangrid1 = Int64MultiArray()
    scangrid2 = Int64MultiArray()
    while not rospy.is_shutdown():
        
        scangrid1.data = delta.read_holding_registers(24032, 32)
        scangrid2.data = delta.read_holding_registers(24064, 32)
        #Wyswietlenie w konsoli
        
        rospy.loginfo("Scangrid data active")

        #Publikowanie wybranych informacji jako topic ROS
        
        scangrid2_pub1.publish(scangrid1)
        scangrid2_pub2.publish(scangrid2)
        rate.sleep()
        clear = lambda: os.system('clear')
        clear()


if __name__ == '__main__':
    try:
        publisher()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)