#!/usr/bin/env python3

import rospy
from std_msgs.msg import Int64, Float32

def test_curtis():
    pub_curtis = rospy.Publisher('comand_curtis_vel', Int64, queue_size=10)
    rospy.init_node('test', anonymous=True)
    rate = rospy.Rate(0.3) # 1hz

    while not rospy.is_shutdown():
        for y in range(-1000, 1000, 100):
            pub_curtis.publish(y)
            rate.sleep()

if __name__ == '__main__':
    try:
        test_curtis()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)