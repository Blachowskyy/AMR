#!/usr/bin/env python3

import threading
import math
from time import sleep
from pyModbusTCP import client
import rospy
from std_msgs.msg import Int64, Float32, Bool
import asyncio

# Do zadawania jazdy wykorzystujemy rejestry %MW101 i %MW102. 
# Rejestr %MW102 przyjmuje wartość 5 lub 6 lub 0 co oznacza kierunek jazdy. 
# 2 to jazda do przodu, 
# 1 to jazda do tyłu, 
# 0 to stop. 
# Rejestr %MW101 przyjmuje wartość 0-4000  prędkość jazdy

class WozekModbusDriver:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.mutex = threading.Lock()
        self.Wozek_Stop = 0
        self.Wozek_do_Tylu = 1 
        self.Wozek_do_Przodu = 2 
        self.Servo_Off = 3333
        self.Servo_On = 4444
        self.Servo_Obrot =  5
        self.direction = 0
        self.speed = 0
        self.pose_reached = False
        self.angle_impulses_old = 0.0
        self.drive_control_status = True
        #Deklaracje subskrybcji wiadomosci z systemu ROS
        try:
            self.deltaPLC = client.ModbusClient(host='192.168.1.4', port=502, auto_open=True, auto_close=True)
            rospy.loginfo("Modbus setup complete")
            self.curtis_sub = rospy.Subscriber('comand_curtis_vel', Int64, self.wozekCallback, queue_size = 10) 
            self.servo_sub = rospy.Subscriber('comand_servo_angle', Float32, self.servoCallback, queue_size = 1)
            self.servo_position_sub = rospy.Subscriber('servo_angle_tick', Float32, self.reads_position)
            self.test_pub = rospy.Publisher('drive_controler_PWM', Int64, queue_size=1)
            self.test2_pub = rospy.Publisher('drive_controler_PWM_callback', Int64, queue_size=1)
            
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)
    def reads_position(self, msg):
        self.servo_actual_position = msg.data
    def pose_validation(self):
        if (self.angle_impulses == self.servo_actual_position):
            self.pose_reached = True
        elif (self.angle_impulses != self.servo_actual_position):
            self.pose_reached = False
        else:
            rospy.loginfo("Pose validation error")
            self.drive_control_status = False
            
    #Modul zaokraglajacy wartosc kata do 2 miejsc po przecinku i pozbywajacy sie przecinka
    def validation_angle_impulses(self):
        self.angle_impulses = round(self.angle_impulses, 2) * 100
        self.angle_impulses = math.trunc(self.angle_impulses)
    #Modul wykonujacy polecenie skretu kola
    def MoveServo(self):
        pose = (f'Servo Pozycja {self.angle_impulses}')
        self.mutex.acquire(blocking=True)
        try:
            self.deltaPLC.write_single_register(116, 0)
            if self.angle_impulses == self.Servo_Off: 
                self.deltaPLC.write_single_register(116, 1)
                rospy.loginfo('Servo Off')
            elif self.angle_impulses != (self.Servo_Off):
                if (self.angle_impulses < 0 and self.angle_impulses >= -90): 
                    self.validation_angle_impulses()
                    rospy.loginfo('minus')
                    self.angle_impulses = self.angle_impulses * -1
                    self.deltaPLC.write_single_register(108, self.angle_impulses)
                    self.deltaPLC.write_single_register(107, 1)
                    rospy.loginfo(pose)
                elif (self.angle_impulses >= 0 and self.angle_impulses <= 90):
                    self.validation_angle_impulses()
                    rospy.loginfo('plus')
                    # self.angle_impulses = self.angle_impulses * -1
                    self.deltaPLC.write_single_register(108, self.angle_impulses)
                    self.deltaPLC.write_single_register(107, 2)
                    rospy.loginfo(pose)
                else: 
                    rospy.loginfo("Value must be in range from -90 to 90")
            self.mutex.release()
            self.angle_impulses_old = self.angle_impulses   
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("MoveServo call failed: %s" % e)
            self.drive_control_status = False
            return False
    #Modul wykonujacy polecenie kierunku i predkosci jazdy
    def MoveMotor(self, direction, speed):
        self.mutex.acquire(blocking=True)
        rospy.loginfo('MoveMotor')
        max_speed =1200
        raczka = self.deltaPLC.read_coils(24576, 1)
        try:
            if self.direction == self.Wozek_do_Przodu:
                if self.speed >= max_speed:
                    self.speed = max_speed
                elif self.speed > 450 and self.speed < max_speed:
                    self.speed = self.speed  
            elif self.direction == self.Wozek_do_Tylu:
                if self.speed <= -max_speed:
                    self.speed = max_speed 
                elif self.speed < -450 and self.speed > -max_speed:
                    self.speed = -self.speed           
            elif raczka == True:
                self.speed = 0
                self.direction = self.Wozek_Stop
            else:
                self.direction = self.Wozek_Stop
                self.speed = 0
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("MoveMotor call failed: %s" % e)
            self.drive_control_status = False
            return False 
        self.deltaPLC.write_single_register(102, self.direction)
        self.deltaPLC.write_single_register(101, self.speed)
        test = self.speed
        self.test_pub.publish(test)
        self.mutex.release()
        rospy.loginfo(f'Predkosc {self.speed} czynnosc {self.direction}')
    #Modul przyjmujacy polecenia skretu kolem
    def servoCallback(self, msg):
        try:
            self.angle_impulses = msg.data
            rospy.loginfo('Servo Callback')   
            self.MoveServo()
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("servoCallback call failed: %s" % e)
            self.drive_control_status = False
            return False
    #Modul przyjmujacy polecenia dotyczace jazdy i okreslajacy jej kierunek
    def wozekCallback(self, msg): 
        self.speed = msg.data
        rospy.loginfo('wozekCallback')
        test = self.speed
        self.test2_pub.publish(test)
        try:
            if self.speed > 450:
                self.direction = self.Wozek_do_Przodu
            elif self.speed < -450:
                self.direction = self.Wozek_do_Tylu     
            else:
                self.speed = 0
                self.direction = self.Wozek_Stop  
            self.MoveMotor(self.direction, self.speed)
            return    
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("wozekCallback call failed: %s" % e)
            self.drive_control_status = False
            return False     
if __name__ == '__main__':
    try:    
        rospy.init_node('wozek_drive_control')
        wozek = WozekModbusDriver()
        drive_control_status_pub = rospy.Publisher('wozek/status', Bool, queue_size=1)
        drive_control_status_pub.publish(wozek.drive_control_status)
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')