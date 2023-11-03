#!/usr/bin/env python3
import rospy
import subprocess
import datetime
import rosbag
import os
from time import sleep
from std_msgs.msg import Int64, Float32

        
class BatteryTester:
    def __init__(self):
        rospy.loginfo_once('Initializing global variables....')
        self.ActualAngle = 0.0
        self.ActualPWM = 0
        self.RequestedAngle = 0.0
        self.TimerStarted = None
        self.ElapsedTIme = None
        self.ActualForksHeight = 0
        self.TimeLimit = 60 * 1
        self.BlockadeFlag = False
        self.ActualSpeed = 0.0
        while not rospy.is_shutdown():
            rospy.loginfo('=================MAIN LOOP================')
            try:
                
                self.forks_height_sub = rospy.Subscriber('Forklift/forks/forks_height', Int64, self.ForksCallback)
                self.ActualSpeedSub = rospy.Subscriber('Forklift/drive/actual_speed', Float32, self.SpeedCallback)
                self.PowerPublisher = rospy.Publisher('Forklift/control/PWM_curtis', Int64, queue_size=1, latch=True)
                self.AnglePublisher = rospy.Publisher('Forklift/control/servo_angle', Float32, queue_size=1, latch=True)
                self.ForksCommandPublisher = rospy.Publisher('Forklift/control/forks', Int64, queue_size=1, latch=True)
            except (rospy.ROSInternalException, rospy.ROSException) as e:
                rospy.loginfo(e)
            self.TimerStarted = rospy.Time.now()
            while True:
                if not self.BlockadeFlag:
                    self.RequestedAngle = 30.0
                    self.ActualPWM = 1000
                    self.AnglePublisherMethod()
                    self.PowerPublisher.publish(self.ActualPWM)
                    rospy.loginfo(self.ActualPWM)
                    self.BlockadeFlag = True
                self.ElapsedTIme = rospy.Time.now() - self.TimerStarted
                if self.ElapsedTIme.to_sec() >= self.TimeLimit:
                    break
            self.BlockadeFlag = False
            while True:
                if not self.BlockadeFlag:
                    self.RequestedAngle = 0.0
                    self.ActualPWM = 0
                    self.PowerPublisher.publish(self.ActualPWM)
                    while True:
                        if self.ActualSpeed == 0.0:
                            sleep(1)
                            break
                    self.AnglePublisherMethod()
                    
                    self.BlockadeFlag = True
                    rospy.loginfo(self.ActualPWM)
                self.ElapsedTIme = rospy.Time.now() - self.TimerStarted
                if self.ElapsedTIme.to_sec() >= 10:
                    break
                if self.ActualSpeed == 0.0:
                    break
            rospy.loginfo('Moving forks')   
            sleep(10)         
            # self.lifting_test()
            self.BlockadeFlag = False
    def AnglePublisherMethod(self):
        self.AnglePublisher.publish(self.RequestedAngle)
        sleep(1)
        while True:
            if self.ActualAngle - self.RequestedAngle > -0.5 or self.ActualAngle - self.RequestedAngle < 0.5:
                break
    def lifting_test(self):
        fork_height_old = self.ActualForksHeight
        test_version = 0
        fork_test_result = False
        rospy.loginfo(fork_height_old)
        if fork_height_old > 150:
            forks_command = 2
            test_version = 1
            self.message = 'Forklift autodiagnostic: Forks lifted more than 200mm, starting dropping test...'
        else:
            forks_command = 1
            test_version = 2
            self.message = 'Forklift autodiagnostic: Starting lifting test...'
        forks_timeout = datetime.datetime.now() + datetime.timedelta(seconds=10)
        self.ForksCommandPublisher.publish(forks_command)
        while True:
            sleep(0.3)           
            if datetime.datetime.now() >= forks_timeout:
                if fork_height_old == self.ActualForksHeight:
                    sleep(1)
                    break  
                elif fork_height_old != self.ActualForksHeight:
                    sleep(0.3)
                    break
        if test_version == 2:
            forks_command = 2
            self.message = 'Forklift autodiagnostic: Dropping test after lifting...'
        else:
            forks_command = 1
            test_version = 2
            self.message = 'Forklift autodiagnostic: Liftiing test after droppinging...'
        sleep(1)
        forks_timeout = datetime.datetime.now() + datetime.timedelta(seconds= 10)
        fork_height_old = self.ActualForksHeight
        self.ForksCommandPublisher.publish(forks_command)
        while True:
            rospy.loginfo(forks_command)
            sleep(0.3)            
            if datetime.datetime.now() >= forks_timeout:
                if fork_height_old == self.ActualForksHeight:
                    sleep(1)
                    break        
                elif fork_height_old != self.ActualForksHeight:
                    break
        if self.ActualForksHeight > 110 and fork_test_result == True:
            sleep(0.2)
            forks_command = 2
            forks_timeout = datetime.datetime.now() + datetime.timedelta(seconds=10)
            self.ForksCommandPublisher.publish(forks_command)
            while True:
                if datetime.datetime.now() >= forks_timeout:
                    if self.ActualForksHeight > 110:
                        break
                    else: 
                        break
                break
        forks_command = 0
        self.ForksCommandPublisher.publish(forks_command)
        if fork_test_result == True:
            sleep(0.2)
            return True
        else:
            sleep(0.2)
            return False
    def ForksCallback(self, msg):
        self.ActualForksHeight = msg.data             
    def SpeedCallback(self, msg):
        self.ActualSpeed = msg.data
    
                    
if __name__ == '__main__':
    try:
        rospy.init_node('BatteryTester')
        rospy.loginfo('===============BATT TESTING STARTED================')
        test = BatteryTester()
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')















