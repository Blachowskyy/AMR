#!/usr/bin/env python3
import rospy
import math
from std_msgs.msg import Int64, Float32
class DriveController:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.MinimalPWM = 350
        self.MaxPWM = 3999
        self.AngleLimit = 90.0
        self.ReceivedAngle = 0.0
        self.ReceivedPWM = 0
        self.CurtisDirection = 0
        self.ServoDirection = 0
        self.ServoPower = 0
        # while not rospy.is_shutdown():
        #     try:
        #         curtisSub = rospy.Subscriber('Forklift/control/PWM_curtis', Int64, self.CurtisCallback)
        #         servoSub = rospy.Subscriber('Forklift/control/servo_angle', Float32, self.ServoCallback)
        #         self.CurtisPWMPub = rospy.Publisher('PLC/write/CurtisPWM', Int64, queue_size=1)
        #         self.CurtisDirectionPub = rospy.Publisher('PLC/write/CurtisDirection', Int64, queue_size=1)
        #         self.ServoPowerPub = rospy.Publisher('PLC/write/ServoPower', Int64, queue_size=1)
        #         self.ServoAnglePub = rospy.Publisher('PLC/write/ServoAngle', Int64, queue_size=1)
        #         self.ServoDirectionPub = rospy.Publisher('PlC/write/ServoDirection', Int64, queue_size=1)
        #     except (rospy.ServiceException, rospy.ROSException) as e:
        #         rospy.logerr(f'Drive controller main exception: {e}')
        try:
            curtisSub = rospy.Subscriber('Forklift/control/PWM_curtis', Int64, self.CurtisCallback, queue_size=1)
            servoSub = rospy.Subscriber('Forklift/control/servo_angle', Float32, self.ServoCallback, queue_size=1)
            self.CurtisPWMPub = rospy.Publisher('PLC/write/CurtisPWM', Int64, queue_size=1)
            self.CurtisDirectionPub = rospy.Publisher('PLC/write/CurtisDirection', Int64, queue_size=1)
            self.ServoPowerPub = rospy.Publisher('PLC/write/ServoPower', Int64, queue_size=1)
            self.ServoAnglePub = rospy.Publisher('PLC/write/ServoAngle', Int64, queue_size=1)
            self.ServoDirectionPub = rospy.Publisher('PLC/write/ServoDirection', Int64, queue_size=1)
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr(f'Drive controller main exception: {e}')
    #Funkcje callback
    def ServoCallback(self, msg):
        self.ReceivedAngle = msg.data
        rospy.loginfo(f'=============================')
        rospy.loginfo(f'       Servo callback')
        rospy.loginfo(f'=============================')
        self.MoveServo()
    def CurtisCallback(self, msg):
        self.ReceivedPWM = msg.data
        if self.ReceivedPWM >= self.MinimalPWM:
            self.CurtisDirection = 1
        elif self.ReceivedPWM <= -self.MinimalPWM:
            self.CurtisDirection = 2
        else:
            self.ReceivedPWM = 0
            self.CurtisDirection = 0
        self.MoveMotor()
    #Konwertery
    def AngleConverter(self):
        self.ReceivedAngle = round(self.ReceivedAngle, 2) * 100
        self.ReceivedAngle = math.trunc(self.ReceivedAngle)
        rospy.loginfo(f'Converted received angle to: {self.ReceivedAngle}')
    #Sterowanie
    def MoveServo(self):
        try:
            if self.ReceivedAngle == 1111:
                self.ServoPower = 1
                self.ServoPowerPub.publish(self.ServoPower)
                rospy.logwarn('Servo power setted to OFF!')
            elif self.ReceivedAngle != 1111:
                self.ServoPower = 0
                self.ServoPowerPub.publish(self.ServoPower)
                rospy.loginfo('Servo power ON')
                if self.ReceivedAngle < 0.0:
                    self.ServoDirection = 1
                    if self.ReceivedAngle < -self.AngleLimit:
                        self.ReceivedAngle = -self.AngleLimit
                        rospy.logwarn('Received higher angle than limit! Setting to max value of -90.0')
                    self.AngleConverter()
                    rospy.loginfo(f'Publishing servo angle: {self.ReceivedAngle}, direction: {self.ServoDirection}')
                    self.ServoAnglePub.publish(self.ReceivedAngle)
                    self.ServoDirectionPub.publish(self.ServoDirection)
                elif self.ReceivedAngle >= 0.0:
                    self.ServoDirection = 2
                    if self.ReceivedAngle > self.AngleLimit:
                        self.ReceivedAngle = self.AngleLimit
                        rospy.logwarn('Receoved higher angle than limit! Setting to max value of 90.0')
                    self.AngleConverter()
                    rospy.loginfo(f'Publishing servo angle: {self.ReceivedAngle}, direction: {self.ServoDirection}')
                    self.ServoAnglePub.publish(self.ReceivedAngle)
                    self.ServoDirectionPub.publish(self.ServoDirection)
                    return
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr(f'Move servo exception: {e}')
            return False
    def MoveMotor(self):
        try:
            if self.CurtisDirection == 1:
                if self.ReceivedPWM >= self.MaxPWM:
                    self.ReceivedPWM = self.MaxPWM
                elif self.ReceivedPWM >= self.MinimalPWM and self.ReceivedPWM < self.MaxPWM:
                    self.ReceivedPWM = self.ReceivedPWM
                rospy.loginfo(f'Curtis direction setted to forward motion')
            elif self.CurtisDirection == 2:
                if self.ReceivedPWM <= -self.MaxPWM:
                    self.ReceivedPWM = self.MaxPWM
                elif self.ReceivedPWM <= -self.MinimalPWM and self.ReceivedPWM > -self.MaxPWM:
                    self.ReceivedPWM = -self.ReceivedPWM
                rospy.loginfo('Curtis direction setted to backward motion')
            else:
                self.CurtisDirection = 0
                self.ReceivedPWM = 0
                rospy.loginfo('Curtis direction setted to stop!')
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr(f'Move servo exception: {e}')
            return False
        self.CurtisDirectionPub.publish(self.CurtisDirection)
        self.CurtisPWMPub.publish(self.ReceivedPWM)
        rospy.loginfo(f'Publishing PWM: {self.ReceivedPWM}')
        return
if __name__ == '__main__':
    try:    
        rospy.init_node('DriveControllerNode')
        driveController = DriveController()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')