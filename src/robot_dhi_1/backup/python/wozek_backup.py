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

class WozekModbusDriver:
    def __init__(self):
        self.mutex = threading.Lock()
        self.Wozek_Stop = 0
        self.Wozek_do_Tylu = 5 
        self.Wozek_do_Przodu = 6 

        self.Servo_Off = 0 
        self.Servo_Zeroj  = 3
        self.Servo_Obrot =  5
        self.direction = 0
        self.speed = 0

        try:
            self.deltaPLC = modbusClient.ModbusClient('192.168.1.4', 502)
            self.deltaPLC.connect()
            self.ecoder = modbusClient.ModbusClient('192.168.1.5', 502)
            self.ecoder.connect()
            rospy.loginfo("Modbus setup complete")
            #subscribers/publishers 
            
            self.pub_comand_curtis_vel = rospy.Publisher('wozek_angle_tick',Int64, queue_size=10, latch=True) 
            self.pub_comand_servo_angle = rospy.Publisher('servo_angle_tick', Int64, queue_size=10, latch=True)
            self.curtis_sub = rospy.Subscriber('comand_curtis_vel', Int64, self.wozekCallback) 
            self.servo_sub = rospy.Subscriber('comand_servo_angle', Int64, self.servoCallback)
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % (e))
            self.end()
    
    def end(self):
        self.deltaPLC.close()
        self.ecoder.close()
        
    def MoveServo(self, angle_impulses, action_type):  
        self.mutex.acquire(blocking=True)
        try:
            if self.angle_impulses == self.Servo_Off:  #Servo_Off = 0
                self.deltaPLC.write_single_register(25041, 0)
                rospy.loginfo('Servo Off')
            elif self.angle_impulses == self.Servo_Zeroj:  #Servo_Zeroj = 3
                self.deltaPLC.write_single_register(25041, 15)
                self.deltaPLC.write_single_register(25042, 1)
                self.deltaPLC.write_single_register(25042, 3)
                rospy.loginfo('Zerowanie kierownicy')
            elif self.angle_impulses != (self.Servo_Off and  self.Servo_Zeroj):
                if self.angle_impulses < 0:
                    rospy.loginfo('Minus')
                    self.deltaPLC.write_single_register(25044, -1)
                    self.deltaPLC.write_single_register(25043, self.angle_impulses)
                    rospy.loginfo(f'Obrot kierownicy o {self.angle_impulses} impulsow')
                else:
                    rospy.loginfo('plus')
                    self.deltaPLC.write_single_register(25044, 0)
                    self.deltaPLC.write_single_register(25043, self.angle_impulses)
                    rospy.loginfo(f'Obrot kierownicy o {self.angle_impulses} impulsow')

                self.deltaPLC.write_single_register(25041, 15)
                self.deltaPLC.write_single_register(25042, 1)
                self.deltaPLC.write_single_register(25042, 5)

            self.mutex.release()

        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("MoveServo call failed: %s" % (e))
            self.end()
            return False 

    def MoveMotor(self, direction, speed):
        self.mutex.acquire(blocking=True)
        rospy.loginfo('MoveMotor')
        try:
            if self.direction == self.Wozek_do_Przodu:
                if self.speed >= 1 and self.speed < 399:
                    self.speed = 400
                     
                elif self.speed > 399:
                    self.speed = self.speed
                    
            elif self.direction == self.Wozek_do_Tylu:
                if self.speed <= -1 and self.speed > -399:
                    self.speed = 400 
                    
                elif self.speed < -399:
                    self.speed = self.speed * -1
                
            else:
                self.direction = self.Wozek_Stop
                self.speed = 0
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("MoveMotor call failed: %s" % (e))
            self.end()
            return False 
        
        rospy.loginfo(f'Predkosc {self.speed} czynnosc {self.direction}')
        self.deltaPLC.write_single_register(25032, self.direction)
        self.deltaPLC.write_single_register(25033, self.speed)
        self.mutex.release()
            
    def servoCallback(self, msg):
        try:
            self.angle_impulses = msg.data
            self.servoAngle = msg.data
            rospy.loginfo('Servo Callback')
            self.MoveServo(self.angle_impulses, self.servoAngle)
        
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("servoCallback call failed: %s" % (e))
            self.end()
            return False

    def wozekCallback(self, msg): 
        self.speed = msg.data
        rospy.loginfo('wozekCallback')
        
        try:
            if self.speed > 0:
                self.direction = self.Wozek_do_Przodu
            elif self.speed < 0:
                self.direction = self.Wozek_do_Tylu     
            else:
                self.direction = self.Wozek_Stop
            
            self.MoveMotor(self.direction, self.speed)
            return 
            
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("wozekCallback call failed: %s" % (e))
            self.end()
            return False

    # def wozekAngleCallback(self, event=None):
    #     try:
    #         msg = Int64()
    #         self.mutex.acquire(blocking=True)
    #         self.encoderTick = self.ecoder.read_holdingregisters(1,1) 
    #         self.a = list(map(int, self.encoderTick ))   
    #         msg.data = self.a[0] 
    #         self.mutex.release()
    #         rospy.loginfo('encoderTick  %s' %msg.data)
        
    #         self.pub_comand_curtis_vel.publish(msg) 
    #     except (rospy.ServiceException, rospy.ROSException) as e:
    #         rospy.logerr("wozekAngleCallback call failed: %s" % (e))
    #         self.end()
    #         return False

    # def servoAngle_Callback(self, event=None):
    #     try:
    #         msg = Int64()
    #         self.mutex.acquire(blocking=True)   
    #         self.servoTick = self.deltaPLC.read_holdingregisters(24038,1)
    #         self.b= list(map(int, self.servoTick))
    #         msg.data = self.b[0] 
    #         self.mutex.release()
    #         rospy.loginfo('servoTick  %s' %msg.data) 
        
    #         self.pub_comand_servo_angle.publish(msg)
    #     except (rospy.ServiceException, rospy.ROSException) as e:
    #         rospy.logerr("servoAngle_Callback call failed: %s" % (e))
    #         self.end()
    #         return False
            
if __name__ == '__main__':
    
    
    try:    
        rospy.init_node('wozek')
        wozek = WozekModbusDriver()
        # rospy.Timer(rospy.Duration(1), wozek.wozekAngleCallback)
        # rospy.Timer(rospy.Duration(1), wozek.servoAngle_Callback)
        rospy.loginfo('+++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % (e))
        
    finally:
        WozekModbusDriver.end()
        rospy.loginfo('+++++++++ OUT++++++++++++++++++')

