#!/usr/bin/env python3

import os
import threading
from time import sleep
import rospy
import math
from sensor_msgs.msg import JointState
from std_msgs.msg import Header, Int64, Float32

class RobotState:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.mutex = threading.Lock()
        self.rate = rospy.Rate(10)
        self.actual_angles = 0.0
        self.actual_radians = 0.0
        self.joints = JointState()
        self.actual_fork_height = 0
        self.actual_fork_height_calibrated = 0
        self.fork_offset = 110
        self.forklift_handle = 0.0
        self.wheel_time = 0.0
        self.wheel_time_old = 0.0
        self.wheel_speed = 0.0
        self.wheel_pose = 0        

        #Deklaracje subskrybcji wiadomosci z systemu ROS
        try:
            
            #Deklaracje subscriberow 
            self.angle_sub = rospy.Subscriber('servo_angle_tick', Float32, self.actual_angle_callback, queue_size = 1) 
            self.fork_sub = rospy.Subscriber('wysokosc_widel', Int64, self.actual_fork_callback, queue_size=1)
            self.steering_sub = rospy.Subscriber('manual_jog', Int64, self.manual_jog_callback, queue_size=1)
            self.wheel_motion_sub = rospy.Subscriber('wheel_motion', Float32, self.wheel_motion_callback, queue_size=1 )
            
            #Deklaracje publisherow
            self.joint_state_pub = rospy.Publisher('joint_states', JointState, queue_size=10)

        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)

        #Wywolanie publishera stanow osi
        self.joint_state_publisher()

    def actual_angle_callback(self, msg): #Odczyt kata skretu kierownicy wozka
        self.actual_angles = msg.data
        rospy.loginfo(self.actual_angles)
        self.actual_radians = (self.actual_angles / 180) * math.pi #Konwersja stopni na radiany
        rospy.loginfo(self.actual_radians)
        rospy.loginfo('spin')

    def actual_fork_callback(self, msg): #Odczyt wysokosci widel
        self.actual_fork_height = msg.data
        self.actual_fork_height_calibrated = ((self.actual_fork_height - self.fork_offset) / 1000) #kalibracja odczytu na ruch
        if (self.actual_fork_height_calibrated < 0):
            self.actual_fork_height_calibrated = self.actual_fork_height_calibrated * 10
        
        #Zabezpieczenie maksymalnych wartosci osi
        if (self.actual_fork_height_calibrated <= -0.02):
            self.actual_fork_height_calibrated = -0.02
        elif (self.actual_fork_height_calibrated > 0.05):
            self.actual_fork_height_calibrated = 0.05
        else:
            self.actual_fork_height_calibrated = self.actual_fork_height_calibrated
        
    def manual_jog_callback(self, msg): #Odczyt trybu recznego wozka ( pochylona kierownica, zolw)
        handle_used = msg.data
        if (handle_used == 0):
            self.forklift_handle = 0.0 #Kierownica pionowo gdy nie w trybie recznym
        elif (handle_used == 1):
            self.forklift_handle = 0.785 #Kierownica pod katem 45 stopni, gdy uzyto trybu recznego
        else:
            rospy.loginfo('Handle error')
    
    def wheel_motion_callback(self, msg): #Odczyt predkosci i przeliczenie na pozycje kolek
        self.wheel_speed = msg.data
        self.wheel_time = rospy.Time.now()
        #Droga przebyta przez kolo - predkosc * (aktualny czas - czas poprzedniego odczytu)
        self.wheel_pose = self.wheel_speed * (self.wheel_time - self.wheel_time_old)
        self.wheel_time_old = self.wheel_time

    def joint_state_publisher(self): #Publikacja stanow osi modelu
        
        #Nieskonczona petla od momentu odpalenia
        while not rospy.is_shutdown():
            try: 

                #Przygotowanie tresci wiadomosci do modelu wozka
                self.joints.header = Header()
                self.joints.header.stamp = rospy.Time.now()
                #Deklaracja nazw osi
                self.joints.name = ['joint_1', 'joint_2', 'joint_3', 'joint_4', 'joint_12'] 
                #Deklaracja pozycji osi zgodnie z kolejnoscia nazw - przypisanie odczytanych i skalibrowanych wartosci
                self.joints.position = [self.actual_radians, self.actual_fork_height_calibrated, self.forklift_handle, self.wheel_pose, (self.wheel_pose * 20)]
                self.joints.effort = [] #Nieuzywane - sila z jaka dzialamy na os zgodnie z kolejnoscia nazw
                self.joints.velocity = [] #nieuzywane - predkosc osi zgodnie z kolejnoscia nazw
                self.joint_state_pub.publish(self.joints)
                rospy.loginfo(self.joints)
                self.rate.sleep()
                clear = lambda: os.system('clear')
                clear()

            except rospy.ROSInternalException as e:
                rospy.loginfo(e)

if __name__ == '__main__':
    try:    
        rospy.init_node('wozek')
        state = RobotState()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')