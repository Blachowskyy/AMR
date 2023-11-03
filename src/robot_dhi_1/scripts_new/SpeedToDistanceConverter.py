#!/usr/bin/env python3
import rospy
from robot_dhi_1.msg import SpeedConverter
import time as T
import datetime as DT
from std_msgs.msg import Float32, Bool
import threading as TH

class DistanceCalculator:
    def __init__(self):
        #Deklaracje zmiennych globalnych
        self.testingPlatform = True
        self.ReceivedData = SpeedConverter()
        self.SendData = SpeedConverter()
        self.ActualSpeed = Float32()
        self.Standstill = Bool()
        self.DateTimeNow = None
        self.DateTimeLast = None
        self.ResetRefPoseThread = TH.Thread(target=self.ResetReference)
        self.ResetRefPoseThread.start()
        while not rospy.is_shutdown():
            #Deklaracja polaczenia
            try: 
                #deklaracja publishera
                self.DistancePub = rospy.Publisher('Forklift/state/distance', SpeedConverter, queue_size=1, latch=True) 
                self.distanceCommandsSub = rospy.Subscriber('Forklift/control/distance', SpeedConverter, self.commandsCallback)  
                self.speedSub = rospy.Subscriber('Forklift/drive/actual_speed', Float32, self.actualSpeedCallback)
                self.standstillSub = rospy.Subscriber('Forklift/state/standtill', Bool, self.standstillCallback)
            except(rospy.ServiceException, rospy.ROSInternalException):
                rospy.loginfo('error')
            # time.sleep(1)
    def commandsCallback(self, msg):
        self.ReceivedData = msg
    def actualSpeedCallback(self, msg):
        speedTmp = msg.data
        if speedTmp >= 0.0 :
            self.ActualSpeed = speedTmp
        elif speedTmp < 0.0 :
            self.ActualSpeed = -speedTmp
    def standstillCallback(self, msg):
        self.Standstill = msg.data
    def ResetReference(self):
        T.sleep(1)
        while not rospy.is_shutdown():
            if self.SendData.ResetReferenceDistance:
                self.SendData.ReferenceMeasure = 0,0
                if self.SendData.ReferenceMeasure == 0.0:
                    self.SendData.ResetReferenceDistanceConfirmation = True
                    rospy.loginfo('Reference position set to 0 !')
                elif self.SendData.ReferenceMeasure != 0.0:
                    self.SendData.ResetReferenceDistanceConfirmation = False
                rospy.loginfo('Error while resseting reference position to 0')
    def totalDistanceCalculator(self):
        T.sleep(1.5)
        while not rospy.is_shutdown():
            if not self.Standstill:
                measureEnd = DT.datetime.now + DT.timedelta(seconds=2)
if __name__ == '__main__':
    try:
        rospy.init_node('DisctanceCalculator')
        distanceCalculator = DistanceCalculator()
        rospy.spin()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Flexi error: %s" % e)