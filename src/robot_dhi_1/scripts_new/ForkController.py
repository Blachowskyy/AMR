#!/usr/bin/env python3

import os
import threading
from time import sleep
import rospy
from std_msgs.msg import Int64, Bool, Int32, String

class forks_module:

    def __init__(self):

        #Deklaracja zmiennych
        self.mutex = threading.Lock()
        self.tilt_1 = 0
        self.tilt_2 = 0
        self.tilt_1_actual = 0
        self.tilt_2_actual = 0
        self.pressure_read = 0
        self.fork_height = 0
        self.fork_ground_level = 105
        self.work_state = 0
        self.standstill = False
        self.forks_height_lim = False
        self.forks_active = False
        self.cargo_state = False
        self.fork_command = 0
        self.fork_stop = 0
        self.rate = rospy.Rate(10) # 10Hz
        #Deklaracje subskrybcji i publikacji wiadomosci z systemu ROS
        try:
            self.work_state_sub = rospy.Subscriber('Forklift/state/workstate_current', Int64, self.work_state_read)
            self.tilt_1_sub = rospy.Subscriber('Forklift/sensors/tilt_axis_1', Int64, self.tilt_1_read)
            self.tilt_2_sub = rospy.Subscriber('Forklift/sensors/tilt_axis_2', Int64, self.tilt_2_read)
            self.pressure_sub = rospy.Subscriber('Forklift/forks/cargo_weight', Int64, self.pressure_reading)
            self.load_command_sub = rospy.Subscriber('Forklift/control/forks', Int64, self.fork_callback)
            self.fork_height_sub = rospy.Subscriber('Forklift/forks/forks_height', Int64, self.fork_height_read)
            self.fork_height_lim_sub = rospy.Subscriber('Forklift/forks/height_limiter', Bool, self.fork_height_lim_read)
            self.stanhdstill_sub = rospy.Subscriber('Forklift/state/standtill', Bool, self.motion_check)
            
            self.forks_command_pub = rospy.Publisher('PLC/write/forks_command', Int64, queue_size=1)
            self.forks_workstate_pub = rospy.Publisher('Forklift/state/forks_workstate', Bool, queue_size=1)
            self.log_message_pub = rospy.Publisher('log/message', String, queue_size=10)
            self.log_level_pub = rospy.Publisher('log/level', Int32, queue_size=10)
            rospy.loginfo("Modbus setup complete")
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)
            self.lifting_modules_status = False
    def work_state_read(self, msg):
        self.work_state = msg.data
    def fork_height_lim_read(self, msg):
        self.forks_height_lim = msg.data
    def motion_check(self, msg):
        self.standstill = msg.data
    #Odczyt topicu o wysokosci widel
    def fork_height_read(self, msg):
        self.fork_height = msg.data
    #Odczyt topicu o przechyle w osi 1
    def tilt_1_read(self, msg):
        self.tilt_1_actual = msg.data
    #Odczyt topicu o przechyle w osi 2
    def tilt_2_read(self, msg):
        self.tilt_2_actual = msg.data
    #Odczyt topicu o czujniku cisnienia
    def pressure_reading(self, msg):
        self.pressure_read = msg.data
    def cargo(self):
        rospy.loginfo('Cargo_check')
        if self.pressure_read > 20:
            self.cargo_state = True
        elif self.pressure_read <= 20:
            self.cargo_state = False
        self.forks_command_pub.publish(self.fork_stop)
    def forks_control(self):
        rospy.loginfo(self.work_state)
        
        self.forks_active = True
        self.forks_workstate_pub.publish(self.forks_active)
        tilt_norm = 5 #Norma stopni odchylu od aktualnego polozenia (5 stopni)
        self.tilt_1 = self.tilt_1_actual #Przypisanie aktualnego odchylenia w osi 1
        self.tilt_2 = self.tilt_2_actual #Przypisanie aktualnego odchylenia w osi 2 
        #Ustawienie maksymalnej wartosci odchylenia +/- w obu osiach
        tilt_1_max = self.tilt_1 + tilt_norm
        tilt_1_min = self.tilt_1 - tilt_norm
        tilt_2_max = self.tilt_2 + tilt_norm
        tilt_2_min = self.tilt_2 - tilt_norm
        if self.standstill == True:
            if self.fork_command == 1:
                while self.tilt_1 < tilt_1_max and self.tilt_1 > tilt_1_min and self.tilt_2 < tilt_2_max and self.tilt_2 > tilt_2_min:
                    if self.forks_height_lim == False:
                        self.forks_command_pub.publish(self.fork_command)
                        if self.forks_height_lim == True:
                            self.cargo()
                            break    
            elif self.fork_command == 2:
                while self.fork_height > self.fork_ground_level:
                    self.forks_command_pub.publish(self.fork_command)
                    if self.fork_height < self.fork_ground_level:
                        self.forks_command_pub.publish(self.fork_stop)
                        self.cargo() 
                        break      
            if self.fork_command == 0:
                self.forks_command_pub.publish(self.fork_stop)
                self.cargo()
            else:
                rospy.loginfo('waiting for stop!')  
        self.rate.sleep()
    #Program odczytujcy polecenie o podniesieniu (1), opuszczeniu (2) oraz przerwaniu pracy (0)
    def fork_callback(self, msg):
        self.fork_command = msg.data
        try:
            self.forks_control()
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("fork calback call failed: %s" % e)
            return False
        rospy.loginfo('++++++++++Forks_LOOP++++++++++')
if __name__ == '__main__':
    try:
        rospy.init_node('forklift_forks', anonymous=True)
        forks = forks_module()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Lifting_module error: %s" % e)
    finally:
        rospy.loginfo('exit')
