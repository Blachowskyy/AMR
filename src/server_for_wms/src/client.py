#!/usr/bin/env python3

import rospy
import socket
import sys
from sick_lidar_localization.msg import LocalizationControllerResultMessage0502

def callback(msg):
    return msg

data = callback()

# Create a connection to the server application on port 81
tcp_socket = socket.create_connection(('localhost', 6060))
rospy.Subscriber("/localizationcontroller/out/localizationcontroller_result_message_0502", 
    LocalizationControllerResultMessage0502, callback)
 
try:
    tcp_socket.sendall(bytes(data, "utf-8"))
    
finally:
    print("Closing socket")
    tcp_socket.close()