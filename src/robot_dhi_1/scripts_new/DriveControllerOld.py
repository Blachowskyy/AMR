#!/usr/bin/env python3

import threading
import math
import rospy
from std_msgs.msg import Int64, Float32, Int32, String

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
        self.Wozek_do_Tylu = 2 
        self.Wozek_do_Przodu = 1 
        self.angle_impulses = 0.0
        self.Servo_Off = 3333
        self.Servo_On = 4444
        self.Servo_Obrot =  5
        self.direction = 0
        self.speed = 0
        self.wysokosc_widel = 0
        
        self.waga = 0
        self.przechyl_bok = 0
        self.przechyl_wzdluz = 0
        self.waga_critical = False
        self.cargo = False
        self.przechyl_danger = False
        self.check_position = False
        self.log_message = ''
        self.log_level = 0
        #Deklaracje subskrybcji wiadomosci z systemu ROS
        try:
            rospy.loginfo("Modbus setup complete")
            self.curtis_sub = rospy.Subscriber('Forklift/control/PWM_curtis', Int64, self.wozekCallback, queue_size = 1) 
            self.servo_sub = rospy.Subscriber('Forklift/control/servo_angle', Float32, self.servoCallback, queue_size = 1)

            self.angle_callback_pub = rospy.Publisher('Forklift/control/feedback/angle_from_base_controller', Int64, queue_size=1)
            self.PWM_received_pub = rospy.Publisher('Forklift/control/feedback/PWM_from_base_controller', Int64, queue_size=1)
            self.curtis_pwm_pub = rospy.Publisher('PLC/write/command_pwm_value', Int64, queue_size=1)
            self.curtis_direction_pub = rospy.Publisher('PLC/write/command_pwm_direction', Int64, queue_size=1)
            self.servo_direction_pub = rospy.Publisher('PLC/write/servo_direction', Int64, queue_size=1)
            self.servo_angle_pub = rospy.Publisher('PLC/write/servo_value', Int64, queue_size=1)
            self.servo_power_pub = rospy.Publisher('PLC/write/servo_power', Int64, queue_size=1)
            self.log_message_pub = rospy.Publisher('log/message', String, queue_size=10)
            self.log_level_pub = rospy.Publisher('log/level', Int32, queue_size=10)
        except (rospy.ServiceException, rospy.ROSException) as e:
            self.log_level = 4
            self.log_message = str(e)
            self.log_level_pub.publish(self.log_level)
            self.log_message_pub.publish(self.log_message)
    #Modul zaokraglajacy wartosc kata do 2 miejsc po przecinku i pozbywajacy sie przecinka
    def validation_angle_impulses(self):
        self.angle_impulses = round(self.angle_impulses, 2) * 100
        self.angle_impulses = math.trunc(self.angle_impulses)
        self.angle_callback_pub.publish(self.angle_impulses)

        
    #Modul wykonujacy polecenie skretu kola
    def MoveServo(self, angle_impulses, action_type):
        pose = (f'Servo Pozycja {self.angle_impulses}')
        try:
            if self.angle_impulses == self.Servo_Off: 
                power = 1
                self.servo_power_pub.publish(power)
                # rospy.loginfo('Servo Off')
            elif self.angle_impulses != (self.Servo_Off):
                power = 0
                self.servo_power_pub.publish(power)
                if (self.angle_impulses < 0 and self.angle_impulses >= -90): 
                    self.validation_angle_impulses()
                    # rospy.loginfo('minus')
                    self.angle_impulses = self.angle_impulses * -1
                    self.servo_angle_pub.publish(self.angle_impulses)
                    self.servo_direction_pub.publish(1)
                    # rospy.loginfo(pose)
                elif (self.angle_impulses >= 0 and self.angle_impulses <= 90):
                    self.validation_angle_impulses()
                    # rospy.loginfo('plus')
                    self.servo_angle_pub.publish(self.angle_impulses)
                    self.servo_direction_pub.publish(2)
                    # rospy.loginfo(pose)
                else:
                    self.log_level = 4
                    self.log_message = "Value must be in range from -90 to 90"
                    self.log_level_pub.publish(self.log_level)
                    self.log_message_pub.publish(self.log_message)    
        except (rospy.ServiceException, rospy.ROSException) as e:
            self.log_level = 4
            self.log_message = str(e)
            self.log_message_pub.publish(self.log_message)
            return False 

    #Modul wykonujacy polecenie kierunku i predkosci jazdy
    def MoveMotor(self, direction, speed):
        
        rospy.loginfo('MoveMotor')
        max_speed =3999
        try:
            if self.direction == self.Wozek_do_Przodu:
                if self.speed >= max_speed:
                    self.speed = max_speed
                elif self.speed >= 350 and self.speed < max_speed:
                    self.speed = self.speed  
            elif self.direction == self.Wozek_do_Tylu:
                if self.speed <= -max_speed:
                    self.speed = max_speed 
                elif self.speed <=350 and self.speed > -max_speed:
                    self.speed = -self.speed 
            else:
                self.direction = self.Wozek_Stop
                self.speed = 0
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("MoveMotor call failed: %s" % e)
            return False 
        self.curtis_direction_pub.publish(self.direction)
        self.curtis_pwm_pub.publish(self.speed)
        # rospy.loginfo(f'Predkosc {self.speed} czynnosc {self.direction}')
    #Modul przyjmujacy polecenia skretu kolem
    def servoCallback(self, msg):
        try:
            servo_position_tmp = 0.0
            self.angle_impulses = msg.data
            self.servoAngle = self.angle_impulses
            rospy.loginfo('Servo Callback')
            self.MoveServo(self.angle_impulses, self.servoAngle)
        except (rospy.ServiceException, rospy.ROSException) as e:
            self.log_level = 4
            self.log_message = "Value must be in range from -90 to 90"
            self.log_level_pub.publish(self.log_level)
            self.log_message_pub.publish(self.log_message)
            return False

    #Modul przyjmujacy polecenia dotyczace jazdy i okreslajacy jej kierunek
    def wozekCallback(self, msg): 
        self.speed = msg.data
        rospy.loginfo('wozekCallback')
        test = self.speed
        self.PWM_received_pub.publish(test)
        try:
            
            if self.speed >= 350:
                self.direction = self.Wozek_do_Przodu
            elif self.speed <= -350:
                self.direction = self.Wozek_do_Tylu     
            else:
                self.speed = 0
                self.direction = self.Wozek_Stop  
            self.MoveMotor(self.direction, self.speed)
            return    
            
        except (rospy.ServiceException, rospy.ROSException) as e:
            self.log_level = 4
            self.log_message = "Value must be in range from -90 to 90"
            self.log_level_pub.publish(self.log_level)
            self.log_message_pub.publish(self.log_message)
            return False

            
if __name__ == '__main__':
    try:    
        rospy.init_node('forklift_drive')
        wozek = WozekModbusDriver()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')