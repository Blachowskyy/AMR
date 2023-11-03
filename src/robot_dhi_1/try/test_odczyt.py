#!/usr/bin/env python3

import rospy 
from std_msgs.msg import Int64, Float32


def callback(data):
    rospy.loginfo("RECEIVED DATA: %s", data.data)

def subscriber():
    rospy.init_node('subscriber_delta', anonymous=True)
    rospy.Subscriber('wozek_angle_tick', Int64, callback)
    rospy.spin()

if __name__ == '__main__':
    try:
        subscriber()
    except rospy.ROSInterruptException:
        pass
