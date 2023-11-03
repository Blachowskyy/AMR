#!/usr/bin/env python3

import rospy
from std_msgs.msg import Int64, Float32


def test_servo():
    pub_servo = rospy.Publisher('comand_servo_angle', Float32, queue_size=10)
    rospy.init_node('test', anonymous=True)
    rate = rospy.Rate(0.1) # 1hz

    while not rospy.is_shutdown():
        for x in range(-70, 70, 139):
            pub_servo.publish(x)
            rate.sleep()

if __name__ == '__main__':
    try:
        test_servo()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)
