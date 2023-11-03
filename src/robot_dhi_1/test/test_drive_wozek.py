#!/usr/bin/env python3

import threading
from easymodbus import modbusClient
import rospy
from std_msgs.msg import Int64

# Do zadawania jazdy wykorzystujemy rejestry D25032 i 25033. 
# Rejestr D25032 przyjmuje wartość 5 lub 6 lub 0 co oznacza kierunek jazdy. 
# 6 to jazda do przodu, 
# 5 to jazda do tyłu, 
# 0 to stop. 
# Rejestr D25033 przyjmuje wartość 0-4000  prędkość jazdy

class ReceivingMessages():

    def __init__(self, direction, speed, angle_impulses):
        self.direction = direction
        self.speed = speed
        self.angle_impulses = angle_impulses

    def servo_callback(self, msg):
        try:
            self.angle_impulses = msg.data
            rospy.loginfo('Servo Callback')
            self.mov(self.servoAngle, self.Servo_Obrot)
        
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("servoCallback call failed: %s" % (e))
            self.end()
            return False

    def wozek_callback(self, msg):
        pass

    servo_sub = rospy.Subscriber('comand_servo_angle', Int64, servo_callback)
    curtis_sub = rospy.Subscriber('comand_curtis_vel', Int64, wozek_callback) 
    

class WozekModbusDriver(ReceivingMessages):

    def __init__(self, direction, speed, angle_impulses, deltaPLC, encoder, mutex, move_forward, move_backwards, move_stop, servo_stop,
    servo_angle, servo_zero):
        super().__init__(direction, speed, angle_impulses)
        self.deltaPLC = deltaPLC
        self.encoder = encoder
        self.mutex = mutex
        self.move_forward = move_forward
        self.move_backwards = move_backwards 
        self.move_stop = move_stop
        self.servo_stop = servo_stop
        self.servo_angle = servo_angle
        self.servo_zero = servo_zero
        move_forward = 5
        move_backwards = 6
        move_stop = 0
        servo_stop = 0
        servo_angle = 5 
        servo_zero = 3

    def connect(self):
        self.deltaPLC = modbusClient.ModbusClient('192.168.1.4', 502)
        self.deltaPLC.connect()
        self.encoder = modbusClient.ModbusClient('192.168.1.5', 502)
        self.encoder.connect()
        rospy.loginfo("Modbus setup complete")
    
    def move_motor(self):
        if self.direction == self.move_forward:
            if self.speed >= 1 and self.speed < 399:
                self.speed = 400
                     
            elif self.speed > 399:
                self.speed = self.speed
                    
        elif self.direction == self.move_backwards:
            if self.speed <= -1 and self.speed > -399:
                self.speed = 400 * -1
                    
            elif self.speed < -399:
                self.speed = self.speed * -1
                
        else:
            self.direction = self.move_stop
            self.speed = 0


    def move_servo(self):
        pass
  

class SendingMessages():
    
    def wozek_angle_tick(self):
        pass

    def servo_angle_tick(self):
        pass


