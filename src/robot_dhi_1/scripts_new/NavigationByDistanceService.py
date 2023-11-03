#!/usr/bin/env python3
import os
import rospy
from time import sleep
from robot_dhi_1.msg import DistanceDrive, Distance
from std_msgs.msg import Float32, Bool, Int64
class DistanceNavigator:
    def __init__(self):
        #Global variables section
        self.DestinationDistance = 0
        self.CurrentDistance = 0
        self.DistancesList = []
        self.CurtisPower = 550
        self.CurtisPowerFromDistance = 0
        self.ServoAngle = 0.0
        self.Enable = False
        self.Start = False
        self.Cancel = False
        self.Reset = False
        self.StartLock = False
        self.ContinuousWork = False
        self.SequenceFinished = False
        self.CommandsSend = DistanceDrive()
        self.Confirmations = DistanceDrive()
        self.Rate = rospy.Rate(10)
        self.CurrentServoAngle = 0.0
        self.CurtisDirection = 0
        self.DistanceV2 = Distance()
        self.PositionReached = False
        
        #Starting infinite program loop
        while not rospy.is_shutdown():
            try:
                # ROS topic subscribers definitions
                distanceSub = rospy.Subscriber('Forklift/DistanceNavigator/Distance', Float32, self.DistanceCallback)
                distanceV2Sub = rospy.Subscriber('Forklift/DistanceNavigator/DistanceV2', Distance, self.DistanceV2Callback)
                curtisPowerSub = rospy.Subscriber('Forklift/DistanceNavigator/PWM', Int64, self.CurtisPowerCallback)
                servoAngleSub = rospy.Subscriber('Forklift/DistanceNavigator/Angle', Float32, self.ServoAngleCallback)
                startDrive = rospy.Subscriber('Forklift/DistanceNavigator/Start', Bool, self.StartCallback)
                # resetSub = rospy.Subscriber('Forklift/DistanceNavigator/Reset', Bool, self.ResetCallback)
                cancelDrive = rospy.Subscriber('Forklift/DistanceNavigator/Cancel', Bool, self.CancelCallback)
                enableSub = rospy.Subscriber('Forklift/DistanceNavigator/Enable', Bool, self.EnableCallback)
                confirmationsSub = rospy.Subscriber('Forklift/DistanceDrive/Read', DistanceDrive, self.ConfirmationsCallback)
                currentServoAngleSub = rospy.Subscriber('Forklift/drive/current_servo_angle', Float32, self.CurrentServoAngleCallback)
                #ROS topic publishers definitions
                self.CommandsSendPub = rospy.Publisher('Forklift/DistanceDrive/Write', DistanceDrive, queue_size=1, latch=True)
                self.CurtisPub = rospy.Publisher('Forklift/control/PWM_curtis', Int64, queue_size=1, latch=True)
                self.ServoPub = rospy.Publisher('Forklift/control/servo_angle', Float32, queue_size=1, latch=True)
                self.PositionReachedPub = rospy.Publisher('Forklift/DistanceDrive/PositionReached', Bool, queue_size=1, latch=True)
            except (rospy.ServiceException, rospy.ROSInternalException, rospy.ROSSerializationException, rospy.ROSTimeMovedBackwardsException) as e:
                rospy.loginfo(f'Exception while running program loop: {e}')
                # rospy.signal_shutdown()
            self.WithLogic()
            self.Rate.sleep()
    def DistanceV2Callback(self, msg):
        data = msg
        if data.Id != self.DistanceV2.Id:
            self.DistanceV2 = data
            self.DistancesList.append(self.DistanceV2.Distance)
            rospy.loginfo(self.DistancesList)
    def CurrentServoAngleCallback(self, msg):
        self.CurrentServoAngle = msg.data
    def StartCallback(self, msg):
        if not self.StartLock:
            self.Start = msg.data
    def ConfirmationsCallback(self, msg):
        self.Confirmations = msg
    # def ResetCallback(self, msg):
    #     self.Reset = msg
    #     sleep(3)
    #     self.Reset = False
    def DistanceCallback(self, msg):
        data = msg.data
        if data != self.DestinationDistance:
            self.DestinationDistance = data
            self.DistancesList.append(self.DestinationDistance)
            rospy.loginfo(self.DistancesList)
        if self.SequenceFinished:
            self.DestinationDistance = data
            self.SequenceFinished = False
            self.DistancesList.append(self.DestinationDistance)
            rospy.loginfo(self.DistancesList)
    def CurtisPowerCallback(self, msg):
        data = msg.data
        if data != self.CurtisPower:
            self.CurtisPower = data
            rospy.loginfo(f'Set curtis power at {self.CurtisPower} PWM')
    def ServoAngleCallback(self, msg):
        data = msg.data
        if data != self.ServoAngle:
            self.ServoAngle = data
            rospy.loginfo(f'Set servo angle at {self.ServoAngle} degrees.')
    def EnableCallback(self, msg):
        self.Enable = msg.data
    def CancelCallback(self, msg):
        self.Cancel = msg.data
    def PublishDataManual(self):
        while self.Start:
            self.StartLock = True
            self.CommandsSend.EnableDistanceDrive = self.Enable
            self.CommandsSend.ResetDistanceDrive = self.Reset
            self.SelectDistance()
            self.CommandsSend.RequestedDistance = self.CurrentDistance
            self.CommandsSend.CancelDistanceDrive = self.Cancel
            self.CommandsSendPub.publish(self.CommandsSend)
            while not self.Confirmations.PositionReached:
                sleep(1)
                if self.Confirmations.PositionReached:
                    break;
    def PublishDistanceData(self):
        rospy.loginfo('Publishing Data Distance commands')
        try:
            self.CommandsSend.EnableDistanceDrive = self.Enable
            self.CommandsSend.ResetDistanceDrive = self.Reset
            self.CommandsSend.RequestedDistance = self.CurrentDistance
            self.CommandsSend.CancelDistanceDrive = self.Cancel
            sleep(0.1)
            self.CommandsSendPub.publish(self.CommandsSend)
        except (Exception) as e:
            rospy.loginfo(f'Exception: {e}')
    def WithLogic(self):
        if len(self.DistancesList) >= 1:
            if not self.ContinuousWork and not self.Confirmations.PositionReached:
                while not self.Start:
                    if self.Start:
                        break
                    sleep(1)
                if self.Start:
                    self.PositionReached = False
                    self.PositionReachedPub.publish(self.PositionReached)
                    sleep(1)
                    self.Enable = self.Start
                    self.StartLock = True
                    
                    rospy.loginfo('Start OK')
                    self.SelectDistance()
                    rospy.loginfo(self.CurrentDistance)
                    if self.CurrentDistance >= 0:
                        self.CurtisPowerFromDistance = self.CurtisPower
                    else:
                        self.CurtisPowerFromDistance = -self.CurtisPower
                    rospy.loginfo(f'Curtis power: {self.CurtisPowerFromDistance}')
                    if self.CurrentDistance < 0:
                        self.CurrentDistance = -self.CurrentDistance
                    self.PublishDistanceData()
                # while not self.Enable:
                #     rospy.loginfo('Waiting for Enable...')
                #     if self.Enable:
                #         sleep(1)
                            
                #         self.PublishDistanceData()
                #         break
                #     sleep(1)
                # if self.Enable:
                    while not self.Confirmations.BasePositionSaved:
                        if self.Confirmations.BasePositionSaved:
                            break
                        sleep(1)
                    if self.Confirmations.BasePositionSaved:
                        servoFinished = False
                        self.ServoPub.publish(self.ServoAngle)
                        while not servoFinished:
                            angleDiff = self.ServoAngle - self.CurrentServoAngle
                            if angleDiff <= 0.1 or angleDiff >= -0.1:
                                servoFinished = True
                                break
                            sleep (0.1)
                        self.CurtisPub.publish(self.CurtisPowerFromDistance)
                        while not self.Confirmations.PositionReached and not self.Cancel:
                            if self.Confirmations.PositionReached:
                                break
                            if self.Cancel:
                                self.CurtisPub.publish(0)
                                break
                            sleep(1)
                            rospy.loginfo('waiting for position')
                        if self.Confirmations.PositionReached or self.Cancel:
                            self.CurtisPub.publish(0)
                            self.Enable = False
                            self.Start = False
                            self.Reset = True
                            self.CurrentDistance = 0.0
                            self.PublishDistanceData()
                                    
                            sleep(1)
                            self.Enable = False
                            self.Start = False
                            self.Reset = False
                            self.PublishDistanceData()
                            self.SequenceFinished = True
                            self.StartLock = False
                            rospy.loginfo('Ending sequence finished')
                            self.PositionReached= True
                            self.PositionReachedPub.publish(self.PositionReached)
                        
        if len(self.DistancesList) <= 0:
            rospy.logerr('DistancesListEmpty')
            sleep(2)                
    def SelectDistance(self):
        if len(self.DistancesList) >= 1:
            self.CurrentDistance = self.DistancesList.pop(0)
            rospy.loginfo(self.DistancesList)
if __name__ == '__main__':
    try:
        rospy.init_node('DistanceNavigator')
        distanceNavigator = DistanceNavigator()
        rospy.spin()
    except rospy.ROSInitException as e:
        rospy.loginfo(f'ROS initialization exception: {e}')
    except rospy.ROSInternalException as e:
        rospy.loginfo(f'ROS internal exception: {e}')
    except Exception as e:
        rospy.loginfo(f'Other exception: {e}')
    finally:
        rospy.loginfo('+++++++++++Distance Navigator: SHUTDOWN++++++++++++')
        # rospy.signal_shutdown()