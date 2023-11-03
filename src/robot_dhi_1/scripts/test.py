#!/usr/bin/env python3
import os
import datetime
from time import sleep
import rospy
from std_msgs.msg import Float32, String, Int32, Time

from pyModbusTCP.client import ModbusClient
from sick_lidar_localization.msg import LocalizationControllerResultMessage0502


def delta_test_64bit():

    deltaPLC = ModbusClient('192.168.1.4', 502, auto_close=True, auto_open=True)
    test = 21.37
    while True:
        deltaPLC.write_multiple_registers(0, test)
        print("true")

   
class Lidarloc():
    def __init__(self):
        self.test = LocalizationControllerResultMessage0502
        while not rospy.is_shutdown():
            test_sub = rospy.Subscriber('/localizationcontroller/out/localizationcontroller_result_message_0502', LocalizationControllerResultMessage0502, self.lidar_listener, queue_size=1)
            self.lidar()
            
            sleep(1)
    def lidar_listener(self, msg):
        self.test = msg
    def lidar(self):
    
        
        data2 = self.test.loc_status
        rospy.loginfo(data2)

        sleep(2)
    
def publisher_angle():
    angle1 = 69.0
    angle2 = -69.0
    angle_execute = 0.0
    rospy.init_node('test', anonymous=True)
    rate = rospy.Rate(5)
    test_pub = rospy.Publisher('comand_servo_angle', Float32, queue_size=1, latch=True)
    while not rospy.is_shutdown():
        if (angle_execute == angle1):
            angle_execute = angle2
        else:
            angle_execute = angle1
        rospy.loginfo(f"Aktualny kat: {angle_execute}")

        endtime = datetime.datetime.now() + datetime.timedelta(seconds =0.2)
        while True:
            if datetime.datetime.now() >= endtime:
                break
            test_pub.publish(angle_execute)

def publisher_logging():
    message = ''
    level = 1
    counter = 0
    rospy.init_node('test', anonymous=True)
    name = 'test'
    rate = rospy.Rate(0.2)
    message_pub = rospy.Publisher('logtopic/message', String, queue_size=1)
    level_pub = rospy.Publisher('logtopic/level', Int32, queue_size=1)
    time_pub = rospy.Publisher('logtopic/time', Time, queue_size=1)

    
    while not rospy.is_shutdown():
        if counter == 0:
            message = "Counter 0"
            last_message = message
        if counter == 5:
            message = last_message
            level = 2
        if counter == 10:
            message = "Counter 10"
            last_message = message
        if counter == 15:
            message = last_message
            level = 1
        if counter == 20:
            message = "Counter 20"
            last_message = message
        if counter == 25:
            message = last_message
            level = 1
        if counter == 30:
            message = "Counter 30"
            last_message = message
        if counter == 35:
            message = last_message
            level = 2
        if counter == 40:
            message = "Counter 40"
            last_message = message
        time = rospy.Time.now()
        time_pub.publish(time)
        level_pub.publish(level)
        message_pub.publish(message)
        counter = counter +1
        rate.sleep()
        rospy.loginfo("error published")
        
if __name__ == '__main__':
    try:
        # rospy.init_node('testing', anonymous=True)
        # lidarloc = Lidarloc()
        # rospy.spin()
        publisher_angle()
        # publisher_logging()
        # delta_test_64bit()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)
