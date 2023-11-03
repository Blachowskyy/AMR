#!/usr/bin/env python3

import os
import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import Int64, String

#ticks - adress (206, 1)

def publisher():
    rospy.init_node('publisherxD', anonymous=True)
    c=ModbusClient(host='192.168.1.4',port=502,auto_open=True)
    rate = rospy.Rate(10) # 1hz
    rospy.loginfo("Publisher Delta Started")

        
    c.write_single_register(110, 1)
    # c.write_single_register(2002, 0)
    rospy.sleep(2)

    rospy.loginfo("Servo enabled")
        

if __name__ == '__main__':
    try:
        publisher()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)
    finally:
        rospy.loginfo('exit')
