#!/usr/bin/env python3
import rospy
import os
from loguru import logger
from time import sleep
from std_msgs.msg import String, Int32, Time

class MyLogger:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.vehicle_id = str(1)
        self.message = ''
        self.level = 0
        self.log_name = ''
        self.log_ready = False
        self.log_time = rospy.Time.now()
        self.data_change = False
        self.message_last = ''
        self.level_last = 0
        self.log_name_last = ''
        self.log_ready_last = False
        self.log_time_last = self.log_time - self.log_time
        self.rate = rospy.Rate(5)
        #Deklaracje subskrybcji wiadomosci z systemu ROS
        try:
            self.log_message_sub = rospy.Subscriber('logtopic/message', String, self.message_callback, queue_size=10)
            self.log_level_sub = rospy.Subscriber('logtopic/level', Int32, self.level_callback, queue_size=10 )
            self.log_name_sub = rospy.Subscriber('logtopic/name', String, self.log_name_callback, queue_size=10)
            self.log_time_sub = rospy.Subscriber('logtopic/time', Time, self.log_time_callback, queue_size=10)
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)
        self.on_data_change()
        
        
    def message_callback(self, msg):
        self.message = msg.data
    def level_callback(self, msg):
        self.level = msg.data
    def log_name_callback(self, msg):
        self.log_name = msg.data
    def log_time_callback(self, msg):
        self.log_time = msg.data   
    def on_data_change(self):
        while not rospy.is_shutdown():
            if self.log_time_last != self.log_time:
                self.data_change = True
                self.logger_info()
            else:
                self.data_change = False
            self.log_time_last = self.log_time
    def opener (self, file, flags):
        return os.open(file, flags, 0o777)

    def logger_info(self):
        while not rospy.is_shutdown():
            self.on_data_change()
            rospy.loginfo(self.data_change)
            while self.data_change == True:
                if (self.level == 1):
                    logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/debug.log", rotation="10000kB", opener = self.opener, format="{time} {level} {message}", level="DEBUG")
                    logger.info(self.message)
                elif (self.level == 2):
                    logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/info.log", rotation="10000kB", opener = self.opener, format="{time} {level} {message}", level="INFO")
                    logger.info(self.message)
                elif (self.level == 3):
                    logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/catkin_ws/src/robot_dhi_1/logs/warning.log", rotation="10000kB", opener = self.opener, format="{time} {level} {message}", level="WARNING")
                    logger.info(self.message)
                elif (self.level == 4):
                    logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/error.log", opener = self.opener, level="ERROR", format="{time} {level} {message}", rotation="10000kB")
                    logger.info(self.message)
                elif (self.level == 5):
                    logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/critical.log", rotation="10000kB", opener = self.opener, format="{time} {level} {message}", level="CRITICAL")
                    logger.info(self.message)
                else:
                    logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/test.log", rotation="10000kB")
                    logger.critical("self.message")
                self.rate.sleep()
            else:
                logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/critical.log", rotation="10000kB", opener = self.opener, format="{time} {level} {message}", level="CRITICAL")
                logger.critical("CRITICAL ERROR IN LOGGER")
                self.rate.sleep()
        
if __name__ == '__main__':
    try:    
        rospy.init_node('logger')
        logger = MyLogger()
        
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')