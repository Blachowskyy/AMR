#!/usr/bin/env python3

from time import sleep
from pyModbusTCP import client
import rospy
from std_msgs.msg import Int64, Float32, Bool, Int32, String
class Encoder:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.speed_actual = 0.0
        self.speed_tmp = 0
        self.encoder_speed = 0
        self.encoder_direction = 0
        self.standstill = False
        self.rate = rospy.Rate(30) # 10Hz
        self.log_message = ''
        self.log_level = 0
        while not rospy.is_shutdown():
            try:
                self.encoder_speed_sub = rospy.Subscriber('PLC/read/encoder_speed', Int64, self.encoder_speed_read)
                self.encoder_direction_sub = rospy.Subscriber('PLC/read/encoder_direction', Int64, self.encoder_direction_read)
                self.actual_speed_pub = rospy.Publisher('Forklift/drive/actual_speed', Float32, queue_size=1)
                self.standstill_pub = rospy.Publisher('Forklift/state/standtill', Bool, queue_size=1)
                self.log_message_pub = rospy.Publisher('log/message', String, queue_size=10)
                self.log_level_pub = rospy.Publisher('log/level', Int32, queue_size=10)
            except(rospy.ServiceException, rospy.ROSException) as e:
                self.log_level = 4
                self.log_message = str(e)
                self.log_level_pub.publish(self.log_level)
                self.log_message_pub.publish(self.log_message)
            self.publishing()        
    def encoder_speed_read(self, msg):
        self.speed_tmp = msg.data    
    def encoder_direction_read(self, msg):
        self.encoder_direction = msg.data  
    def publishing(self):
        rospy.loginfo(self.encoder_direction)
        if self.encoder_direction == 1:
            self.speed_actual = round((self.speed_tmp / 100), 2)
        elif self.encoder_direction == 2:
            self.speed_actual = round((self.speed_tmp / (-100)), 2)
        else:
            rospy.loginfo(self.encoder_direction)
            self.log_level = 4
            self.log_message = 'Encoder read error: encoder direction'
            self.log_level_pub.publish(self.log_level)
            self.log_message_pub.publish(self.log_message)
        if self.speed_actual != 0.0:
            self.standstill = False
        else:
            self.standstill = True
        self.actual_speed_pub.publish(self.speed_actual)
        self.standstill_pub.publish(self.standstill)
        rospy.loginfo('++++++++++ ENCODER LOOP +++++++')
        self.rate.sleep()                   
if __name__ == '__main__':
    try:    
        rospy.init_node('encoder_read')
        encoder = Encoder()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e) 
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')