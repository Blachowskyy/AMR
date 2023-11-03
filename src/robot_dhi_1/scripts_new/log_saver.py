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
        self.log_time = 0.0
        self.data_change = False
        self.message_last = ''
        self.level_last = 0
        self.log_name_last = ''
        self.log_ready_last = False
        self.log_time_last = 0.0
        self.rate = rospy.Rate(3)
        logger.add("/home/ros/catkin_ws/src/robot_dhi_1/logs/forklift.log", rotation="200MB", format="{time} {level} {message}", level="DEBUG")
        while not rospy.is_shutdown():
             
            try:
                #Deklaracje subskrybcji wiadomosci z systemu ROS
                self.log_message_sub = rospy.Subscriber('log/message', String, self.message_callback, queue_size=10)
                self.log_level_sub = rospy.Subscriber('log/level', Int32, self.level_callback, queue_size=10)
            except (rospy.ServiceException, rospy.ROSException) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
            self.on_data_change()
    #Odczyt subscriberow
    def message_callback(self, msg):
        self.message = msg.data
        self.log_time = rospy.get_time()
    def level_callback(self, msg):
        self.level = msg.data
    def log_name_callback(self, msg):
        self.log_name = msg.data
    #Start sprawdzenie, czy nastapila nowa wiadomosc
    def on_data_change(self):
                #Sprawdzenie warunku czasu wiadomosci
                if self.log_time_last != self.log_time:
                    self.data_change = True
                    #Uruchomienie programu zapisujacego wiadomosc do pliku
                    self.logger_info()
                    #Zapis czasu wiadomosci jako ostatni czas
                    self.log_time_last = self.log_time
                # else: 
                #     rospy.loginfo("Waiting on data")
                #Czas odswiezania
                self.rate.sleep()
    #Zapis do pliku
    def logger_info(self):
            #Jesli nastapila zmiana czasu wiadomosci
            if self.data_change == True:
                #Sprawdzenie, czy ostatnia wiadomosc nie ma tej samej tresci lub poziomu
                if self.message != self.message_last or self.level != self.level_last:
                    #Sortowanie wiadomosci po poziomie i zapis
                    if (self.level == 1):
                        logger.debug(self.message)
                    elif (self.level == 2):
                        logger.info(self.message)
                    elif (self.level == 3):
                        logger.warning(self.message)
                    elif (self.level == 4):
                        logger.error(self.message)
                    elif (self.level == 5):
                        logger.critical(self.message)
                    #Jesli poziom nie wystepuje w wartosci 1-5, zapisz blad o bledzie poziomu
                    else:
                        logger.critical("problem with error level")
                #Zapamietanie ostatniej wiadomosci i poziomu oraz czas odswiezania
                self.message_last = self.message
                self.level_last = self.level
                self.rate.sleep()
                #Wyjscie z funkcji, wylaczenie potwierdzenia zmiany czasu wiadomosci w celu ponownego sprawdzenia
                self.data_change = False
            
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