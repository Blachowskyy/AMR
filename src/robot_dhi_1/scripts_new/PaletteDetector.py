#!/usr/bin/env python3

from time import sleep
import rospy 
import os
import asyncio
import datetime as DT
from std_msgs.msg import Bool, Int64MultiArray, Int64
from robot_dhi_1.msg import Palette
class PaletteDetector:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.ScangridLeftValues = Int64MultiArray()
        self.ScangridRightValues = Int64MultiArray()
        self.SearchRange0 = 0
        self.SearchRange1 = 0
        self.SearchRange2 = 0
        self.DistanceNow = 0
        self.DistanceLast = 0
        self.Disturbance = 150
        self.DistanceNowSecondary = 0
        self.DistanceLastSecondary = 0
        self.Palette = Palette()
        self.PaletteList = []
        self.BaseExpectedDistance = 510
        self.Palette1ExpectedDistance = 0
        self.Palette2ExpectedDistance = 0
        self.Palette3ExpectedDistance = 0
        self.PaletteSide = 1
        self.Rate = rospy.Rate(1)
        self.palette1 = Palette()
        self.palette2 = Palette()
        self.palette3 = Palette()
        self.LastDistance2 = 0
        self.LastDistance3 = 0
        try:
            distanceSub = rospy.Subscriber('PLC/read/distance', Int64, self.DistanceCallback)
            scangridRightSub = rospy.Subscriber('PLC/read/scangrid1ranges', Int64MultiArray, self.RightScangridCallback)
            scangridLeftSub = rospy.Subscriber('PLC/read/scangrid2ranges', Int64MultiArray, self.LeftScangridCallback)
        except(rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)
        rospy.loginfo('Starting detection...')
        self.Detection()
        self.Rate.sleep()
    def DistanceCallback(self, msg):
        self.DistanceNow = msg.data
    def RightScangridCallback(self, msg):
        self.ScangridRightValues = msg
    def LeftScangridCallback(self, msg):
        self.ScangridLeftValues = msg
    def AverageMeasurings(self):
        rospy.loginfo('Counting palettes OK...')
        palletsCounter = 0
        if self.palette1.PaletteOk:
            self.Palette.EndDistance = self.Palette.EndDistance + self.palette1.EndDistance
            self.Palette.StartDistance = self.Palette.StartDistance + self.palette1.StartDistance
            self.Palette.FirstBlockLength = self.Palette.FirstBlockLength + self.palette1.FirstBlockLength
            self.Palette.FirstForkSpace = self.Palette.FirstForkSpace + self.palette1.FirstForkSpace
            self.Palette.SecondaryBlockLength = self.Palette.SecondaryBlockLength + self.palette1.SecondaryBlockLength
            self.Palette.SecondForkSpace = self.Palette.SecondForkSpace + self.palette1.SecondForkSpace
            self.Palette.ThirdBlockLength = self.Palette.ThirdBlockLength + self.palette1.ThirdBlockLength
            self.Palette.OverallLength = self.Palette.OverallLength + self.palette1.OverallLength
            palletsCounter += 1
        if self.palette2.PaletteOk:
            self.Palette.EndDistance = self.Palette.EndDistance + self.palette2.EndDistance
            self.Palette.StartDistance = self.Palette.StartDistance + self.palette2.StartDistance
            self.Palette.FirstBlockLength = self.Palette.FirstBlockLength + self.palette2.FirstBlockLength
            self.Palette.FirstForkSpace = self.Palette.FirstForkSpace + self.palette2.FirstForkSpace
            self.Palette.SecondaryBlockLength = self.Palette.SecondaryBlockLength + self.palette2.SecondaryBlockLength
            self.Palette.SecondForkSpace = self.Palette.SecondForkSpace + self.palette2.SecondForkSpace
            self.Palette.ThirdBlockLength = self.Palette.ThirdBlockLength + self.palette2.ThirdBlockLength
            self.Palette.OverallLength = self.Palette.OverallLength + self.palette2.OverallLength
            palletsCounter += 1
        if self.palette3.PaletteOk:
            self.Palette.EndDistance = self.Palette.EndDistance + self.palette3.EndDistance
            self.Palette.StartDistance = self.Palette.StartDistance + self.palette3.StartDistance
            self.Palette.FirstBlockLength = self.Palette.FirstBlockLength + self.palette3.FirstBlockLength
            self.Palette.FirstForkSpace = self.Palette.FirstForkSpace + self.palette3.FirstForkSpace
            self.Palette.SecondaryBlockLength = self.Palette.SecondaryBlockLength + self.palette3.SecondaryBlockLength
            self.Palette.SecondForkSpace = self.Palette.SecondForkSpace + self.palette3.SecondForkSpace
            self.Palette.ThirdBlockLength = self.Palette.ThirdBlockLength + self.palette3.ThirdBlockLength
            self.Palette.OverallLength = self.Palette.OverallLength + self.palette3.OverallLength
            palletsCounter += 1
        rospy.loginfo(f'Number of OK palettes: {palletsCounter}')
        rospy.loginfo('Making average dimensions...')
        if palletsCounter >= 2:
            self.Palette.EndDistance = self.Palette.EndDistance / palletsCounter
            self.Palette.StartDistance = self.Palette.StartDistance / palletsCounter
            self.Palette.FirstBlockLength = self.Palette.FirstBlockLength / palletsCounter
            self.Palette.FirstForkSpace = self.Palette.FirstForkSpace / palletsCounter
            self.Palette.SecondaryBlockLength = self.Palette.SecondaryBlockLength / palletsCounter
            self.Palette.SecondForkSpace = self.Palette.SecondForkSpace / palletsCounter
            self.Palette.ThirdBlockLength = self.Palette.ThirdBlockLength / palletsCounter
            self.Palette.OverallLength = self.Palette.OverallLength / palletsCounter
            rospy.loginfo('================================================================')
            rospy.loginfo('                 PRINTING AVERAGE DIMENSIONS')
            rospy.loginfo('================================================================')
            rospy.loginfo(self.Palette)
    def Detection(self):
        if self.PaletteSide == 1:
            palette1 = Palette()
            palette2 = Palette()
            palette3 = Palette()
            methodStartDistance = 0
            self.Palette1ExpectedDistance = self.BaseExpectedDistance
            self.Palette2ExpectedDistance = self.BaseExpectedDistance
            self.Palette3ExpectedDistance = self.BaseExpectedDistance
            startDistanceSaved = False
            difference1 = 0
            difference2 = 0
            while True:
                rospy.loginfo_once('Waiting for palette first edge...')
                if self.ScangridLeftValues.data != None and len(self.ScangridLeftValues.data) >= 3:
                    self.SearchRange0 = self.ScangridLeftValues.data[0]
                    self.SearchRange1 = self.ScangridLeftValues.data[1]
                    self.SearchRange2 = self.ScangridLeftValues.data[2]
                #First range palette monitoring logic
                if self.SearchRange0 <= self.Palette1ExpectedDistance and not self.SearchRange0 == 0:
                    palette1.StartDistance = self.DistanceNow
                    palette1.FirstBlockDistance = self.SearchRange0
                    if not startDistanceSaved:
                        methodStartDistance = self.DistanceNow
                        startDistanceSaved = True
                        rospy.loginfo(f'Method start distance 1 = {startDistanceSaved}')
                if not palette1.FirstBlockDetected:
                    if self.SearchRange0 > (self.Palette1ExpectedDistance + self.Disturbance) and palette1.StartDistance != 0:
                        palette1.FirstBlockLength = self.DistanceNow - palette1.StartDistance
                        palette1.FirstBlockDetected = True
                if palette1.FirstBlockDetected and not palette1.MiddleBlockDetected:
                    if self.SearchRange0 <= self.Palette1ExpectedDistance and palette1.FirstForkSpace == 0:
                        palette1.FirstForkSpace = self.DistanceNow - palette1.StartDistance - palette1.FirstBlockLength
                    if palette1.FirstForkSpace > 0 and self.SearchRange0 > (self.Palette1ExpectedDistance + self.Disturbance):
                        palette1.SecondaryBlockLength = self.DistanceNow - palette1.StartDistance - (palette1.FirstBlockLength + palette1.FirstForkSpace)
                        palette1.MiddleBlockDetected = True
                if palette1.FirstBlockDetected and palette1.MiddleBlockDetected and not palette1.LastBlockDetected:
                    if self.SearchRange0 <= self.Palette1ExpectedDistance and palette1.SecondForkSpace == 0:
                        palette1.SecondForkSpace = self.DistanceNow - palette1.StartDistance - (palette1.FirstBlockLength + palette1.FirstForkSpace + palette1.SecondaryBlockLength)
                    if palette1.SecondForkSpace != 0 and self.SearchRange0 > ( self.Palette1ExpectedDistance + self.Disturbance):
                        palette1.ThirdBlockLength = self.DistanceNow - palette1.StartDistance - (palette1.FirstBlockLength + palette1.FirstForkSpace + palette1.SecondaryBlockLength + palette1.SecondForkSpace)
                        palette1.LastBlockDetected = True
                if palette1.FirstBlockDetected and palette1.MiddleBlockDetected and not palette1.LastBlockDetected:
                    palette1.EndDistance = self.DistanceNow
                    palette1.OverallLength = palette1.EndDistance - palette1.StartDistance
                    palette1.PaletteOk = True
                if palette1.PaletteOk:
                    rospy.loginfo_once('===============PALETTE 1 FINALL DATA===============')
                    rospy.loginfo_once(palette1)
                #Second range palette measuring logic
                if self.SearchRange1 <= self.Palette2ExpectedDistance and self.SearchRange1 !=0:
                    if palette2.StartDistance == 0:
                        palette2.StartDistance = self.DistanceNow
                        palette2.FirstBlockDistance = self.SearchRange1
                        rospy.loginfo(palette2.FirstBlockDistance)
                        if not startDistanceSaved:
                            methodStartDistance = self.DistanceNow
                            startDistanceSaved = True
                            rospy.loginfo(f'Method start distance 2 = {startDistanceSaved}')
                if palette2.FirstBlockDistance > self.SearchRange1 and palette2.StartDistance != 0:
                    palette2.FirstBlockDistance = self.SearchRange1
                    difference1 = self.Palette2ExpectedDistance - palette2.FirstBlockDistance
                # if difference1 > 20:
                #     self.Palette2ExpectedDistance = self.Palette2ExpectedDistance - (difference1 + 20)
                if not palette2.FirstBlockDetected and palette2.StartDistance != 0:
                    if self.SearchRange1 > (self.Palette2ExpectedDistance + self.Disturbance):
                        palette2.FirstBlockLength = self.DistanceNow - palette2.StartDistance
                        palette2.FirstBlockDetected = True
                        # rospy.loginfo(f'FIRSTBLOCKLENGTH: {palette2}')
                if palette2.FirstBlockDetected and not palette2.MiddleBlockDetected:
                    if self.SearchRange1 <= self.Palette2ExpectedDistance and palette2.FirstForkSpace == 0:
                        palette2.FirstForkSpace = self.DistanceNow - palette2.StartDistance - palette2.FirstBlockLength
                        palette2.SecondBlockDistance = self.SearchRange1
                        rospy.loginfo(palette2.SecondBlockDistance)
                        distancediff = palette2.SecondBlockDistance - palette2.FirstBlockDistance
                        if distancediff > 0:
                            self.Palette2ExpectedDistance = self.Palette2ExpectedDistance + distancediff
                        if distancediff < 0:
                            self.Palette2ExpectedDistance = self.Palette2ExpectedDistance - distancediff
                    if palette2.FirstForkSpace > 0 and self.SearchRange1 > (self.Palette2ExpectedDistance + self.Disturbance):
                        palette2.SecondaryBlockLength = self.DistanceNow - palette2.StartDistance - (palette2.FirstBlockLength + palette2.FirstForkSpace)
                        palette2.MiddleBlockDetected = True
                if palette2.FirstBlockDetected and palette2.MiddleBlockDetected and not palette2.LastBlockDetected:
                    if self.SearchRange1 <= self.Palette2ExpectedDistance and palette2.SecondForkSpace == 0:
                        palette2.SecondForkSpace = self.DistanceNow - palette2.StartDistance - (palette2.FirstBlockLength + palette2.FirstForkSpace + palette2.SecondaryBlockLength)
                    if palette2.SecondForkSpace != 0 and self.SearchRange1 > ( self.Palette2ExpectedDistance + self.Disturbance):
                        palette2.ThirdBlockLength = self.DistanceNow - palette2.StartDistance - (palette2.FirstBlockLength + palette2.FirstForkSpace + palette2.SecondaryBlockLength + palette2.SecondForkSpace)
                        palette2.LastBlockDetected = True
                if palette2.FirstBlockDetected and palette2.MiddleBlockDetected and palette2.LastBlockDetected:
                    palette2.EndDistance = self.DistanceNow
                    palette2.OverallLength = palette2.EndDistance - palette2.StartDistance
                    palette2.PaletteOk = True
                if palette2.PaletteOk:
                    rospy.loginfo_once('===============PALETTE 2 FINALL DATA===============')
                    rospy.loginfo_once(palette2) 
                #Third range palette measuring logic
                if self.SearchRange2 <= self.Palette3ExpectedDistance and self.SearchRange2 != 0:
                    if palette3.StartDistance == 0:
                        palette3.StartDistance = self.DistanceNow
                        palette3.FirstBlockDistance = self.SearchRange2
                        if not startDistanceSaved:
                            methodStartDistance = self.DistanceNow
                            startDistanceSaved = True
                            rospy.loginfo(f'Method start distance 3= {startDistanceSaved}')
                if palette3.FirstBlockDistance > self.SearchRange2 and palette3.StartDistance != 0:
                    palette3.FirstBlockDistance = self.SearchRange2
                    difference2 = self.Palette3ExpectedDistance - palette3.FirstBlockDistance
                # if difference2 > 20:
                #     self.Palette2ExpectedDistance = self.Palette2ExpectedDistance - (difference2 + 20)
                if not palette3.FirstBlockDetected and palette3.StartDistance != 0: 
                    if self.SearchRange2 > (self.Palette3ExpectedDistance + self.Disturbance):
                        palette3.FirstBlockLength = self.DistanceNow - palette3.StartDistance
                        palette3.FirstBlockDetected = True
                if palette3.FirstBlockDetected and not palette3.MiddleBlockDetected:
                    if self.SearchRange2 <= self.Palette3ExpectedDistance and palette3.FirstForkSpace == 0:
                        palette3.FirstForkSpace = self.DistanceNow - palette3.StartDistance - palette3.FirstBlockLength
                        distancediff = palette3.SecondBlockDistance - palette3.FirstBlockDistance
                        if distancediff > 0:
                            self.Palette3ExpectedDistance = self.Palette3ExpectedDistance + distancediff
                        if distancediff < 0:
                            self.Palette3ExpectedDistance = self.Palette3ExpectedDistance - distancediff
                    if palette3.FirstForkSpace > 0 and self.SearchRange2 > (self.Palette3ExpectedDistance + self.Disturbance):
                        palette3.SecondaryBlockLength = self.DistanceNow - palette3.StartDistance - (palette3.FirstBlockLength + palette3.FirstForkSpace)
                        palette3.MiddleBlockDetected = True
                if palette3.FirstBlockDetected and palette3.MiddleBlockDetected and not palette3.LastBlockDetected:
                    if self.SearchRange2 <= self.Palette3ExpectedDistance and palette3.SecondForkSpace == 0:
                        palette3.SecondForkSpace = self.DistanceNow - palette3.StartDistance - (palette3.FirstBlockLength + palette3.FirstForkSpace + palette3.SecondaryBlockLength)
                    if palette3.SecondForkSpace != 0 and self.SearchRange2 > ( self.Palette3ExpectedDistance + self.Disturbance):
                        palette3.ThirdBlockLength = self.DistanceNow - palette3.StartDistance - (palette3.FirstBlockLength + palette3.FirstForkSpace + palette3.SecondaryBlockLength + palette3.SecondForkSpace)
                        palette3.LastBlockDetected = True
                if palette3.FirstBlockDetected and palette3.MiddleBlockDetected and palette3.LastBlockDetected:
                    palette3.EndDistance = self.DistanceNow
                    palette3.OverallLength = palette3.EndDistance - palette3.StartDistance
                    palette3.PaletteOk = True
                if palette3.PaletteOk:
                    rospy.loginfo_once('===============PALETTE 3 FINALL DATA===============')
                    rospy.loginfo_once(palette3)
                if (palette3.PaletteOk and palette2.PaletteOk) or (palette1.PaletteOk and palette2.PaletteOk) or (palette1.PaletteOk and palette3.PaletteOk ):
                    self.palette1 = palette1
                    self.palette2 = palette2
                    self.palette3 = palette3
                    break
                # if (self.DistanceNow - methodStartDistance) > 1100:
                #     rospy.loginfo('Method distance too long. abroting')
                #     break
                
if __name__ == '__main__':
    try:    
        rospy.init_node('PaletteDetectionNode')
        paletteDetector = PaletteDetector()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        