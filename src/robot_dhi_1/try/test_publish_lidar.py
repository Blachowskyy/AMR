#!/usr/bin/env python
import rospy
from sick_lidar_localization.msg import LocalizationControllerResultMessage0502


def callback(data):
    rospy.loginfo(rospy.get_caller_id() + "I heard %s", data.x)
    
def listener():
    rospy.init_node('listener', anonymous=True)
    rospy.Subscriber("/localizationcontroller/out/localizationcontroller_result_message_0502", 
    LocalizationControllerResultMessage0502, callback)
    rospy.spin()

if __name__ == '__main__':
    listener()

        