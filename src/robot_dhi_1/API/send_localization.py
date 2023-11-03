#!/usr/bin/env python3

import requests
import rospy
from sick_lidar_localization.msg import LocalizationControllerResultMessage0502


def send_loc(msg):
    URL = "http://192.168.3.38:2137/app/current"
    pose = {'pose_x':msg.x, 'pose_y':msg.y, 'pose_yaw':msg.heading}
    
    r = requests.post(URL, json= pose)

def listener():
    rospy.init_node('listener', anonymous=True)
    rospy.Subscriber("/localizationcontroller/out/localizationcontroller_result_message_0502", 
    LocalizationControllerResultMessage0502, send_loc)
    rospy.spin()


if __name__ == '__main__':
    listener()