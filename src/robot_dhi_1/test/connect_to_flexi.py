#!/usr/bin/env python3

import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import String

def publisher():
    pub = rospy.Publisher('flexi_topic', String, queue_size=10)
    rospy.init_node('publisher', anonymous=True)
    #Connection with plc
    c=ModbusClient(host='192.168.1.11',port=502,auto_open=True)

    rate = rospy.Rate(1) # 1hz
    rospy.loginfo("Publisher Flexi Started")

    while not rospy.is_shutdown():
        # Odczyt z encodra kola
        regs = c.read_holding_registers(999,101)
        msg = ("Reading register values {}".format(regs))
        rospy.loginfo(msg)
        pub.publish(msg)
        rate.sleep()

if __name__ == '__main__':
    try:
        publisher()
    except rospy.ROSInterruptException:
        pass
