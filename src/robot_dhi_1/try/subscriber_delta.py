#!/usr/bin/env python

import rospy
from std_msgs.msg import String

def callback(data):
    rospy.loginfo("RECEIVED DATA: %s", data.data)

def subscriber():
    rospy.init_node('subscriber_delta', anonymous=True)
    rospy.Subscriber('delta_topic', String, callback)
    rospy.spin()

if __name__ == '__main__':
    try:
        subscriber()
    except rospy.ROSInterruptException:
        pass
