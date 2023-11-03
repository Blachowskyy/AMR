#!/usr/bin/env python3

from time import sleep
import rospy 
import os
import datetime as DT
from std_msgs.msg import Bool, Float32, Int64
from robot_dhi_1.msg import LogMessages, Distance

class DistanceTester:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.logToSend = LogMessages()
        self.PWM = 600
        self.Angle = 2.5
        self.Distance1 = 14500.0
        self.Distance2 = -14500.0
        self.DistanceSend = Distance()
        self.Id = 1
        self.Counter = 1
        self.Stop = False
        # while not rospy.is_shutdown:
        #     try:
        #         self.distancePub = rospy.Publisher('Forklift/DistanceNavigator/Distance', Float32, queue_size=1)
        #         self.curtisPowerPub = rospy.Publisher('Forklift/DistanceNavigator/PWM', Int64, queue_size=1)
        #         self.servoAnglePub = rospy.Publisher('Forklift/DistanceNavigator/Angle', Float32, queue_size=1)
        #         self.startDrivePub = rospy.Publisher('Forklift/DistanceNavigator/Start', Bool, queue_size=1)
        #         self.resetPub = rospy.Publisher('Forklift/DistanceNavigator/Reset', Bool, queue_size=1)
        #         self.cancelDrivePub = rospy.Publisher('Forklift/DistanceNavigator/Cancel', Bool, queue_size=1)
        #         self.enablePub = rospy.Publisher('Forklift/DistanceNavigator/Enable', Bool, queue_size=1)        
        #     except(rospy.ServiceException, rospy.ROSException) as e:
        #         rospy.logerr("connect/subscribers/publishers: %s" % e)
        #     rospy.loginfo('Creating log...')
        #     while not self.Stop:
        #         self.PublishTest()
        #         self.Stop = True
        #         if self.Stop:
        #             break
        #     break
        
        try:
            self.distancePub = rospy.Publisher('Forklift/DistanceNavigator/DistanceV2', Distance, queue_size=1, latch=True)
            self.curtisPowerPub = rospy.Publisher('Forklift/DistanceNavigator/PWM', Int64, queue_size=1, latch=True)
            self.servoAnglePub = rospy.Publisher('Forklift/DistanceNavigator/Angle', Float32, queue_size=1, latch=True)
            self.startDrivePub = rospy.Publisher('Forklift/DistanceNavigator/Start', Bool, queue_size=1, latch=True)
            self.resetPub = rospy.Publisher('Forklift/DistanceNavigator/Reset', Bool, queue_size=1, latch=True)
            self.cancelDrivePub = rospy.Publisher('Forklift/DistanceNavigator/Cancel', Bool, queue_size=1, latch=True)
            self.enablePub = rospy.Publisher('Forklift/DistanceNavigator/Enable', Bool, queue_size=1, latch=True)        
        except(rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)
        self.PublishTest()

    def PublishTest(self):
        self.DistanceSend.Id = self.Id
        self.DistanceSend.Distance = -self.Distance1

        self.distancePub.publish(self.DistanceSend)
        sleep(1)
        for r in range (0, 5):
            rospy.loginfo(r)
            if self.DistanceSend.Distance >0:
                self.Id +=1
                self.DistanceSend.Id = self.Id
                self.DistanceSend.Distance = -self.Distance1
            else:
                self.Id +=1
                self.DistanceSend.Id = self.Id
                self.DistanceSend.Distance = self.Distance1
            self.distancePub.publish(self.DistanceSend)   
            sleep(1)
        # self.DistanceSend.Id = self.Id
        # self.DistanceSend.Distance = -self.Distance1
        # self.distancePub.publish(self.DistanceSend)
                       
if __name__ == '__main__':
    try:    
        rospy.init_node('DistanceTester')
        distanceTeste = DistanceTester()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        