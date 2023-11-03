#!/usr/bin/env python3

from time import sleep
import rospy
from std_msgs.msg import Int64MultiArray, Int64, Bool
from robot_dhi_1.msg import Palette, Scangrids

class PalletScanner:
    def __init__(self):
        #Global variables 
        self.LeftScangridValues = Int64MultiArray()
        self.RightScangridValues = Int64MultiArray()
        self.ScangridsDataIn = Scangrids()
        self.SearchRange0 = 0
        self.SearchRange1 = 0
        self.SearchRange2 = 0
        self.DistanceNow = 0
        self.ReadingSpike = 50
        self.MainPalette = Palette()
        self.PalletesList = []
        self.BasePaletteExpectedDistance = 500
        self.PaletteSearchSide = 1
        self.Rate = rospy.Rate(1)
        self.PaletteArea1 = Palette()
        self.PaletteArea2 = Palette()
        self.PaletteArea3 = Palette()
        self.DistancesListArea0 = []
        self.DistancesListArea1 = []
        self.DistancesListArea2 = []
        self.DistancesListArea29 = []
        self.DistancesListArea30 = []
        self.DistancesListArea31 = []
        self.SaveDistancesArea0 = False
        self.SaveDistancesArea1 = False
        self.SaveDistancesArea2 = False
        self.SaveDistancesArea29 = False
        self.SaveDistancesArea30 = False
        self.SaveDistancesArea31 = False
        self.SinglePaletteMode = True
        self.StackPallets = False
        self.StartScan = False
        self.PatternPalettte = Palette()
        self.PatternPalettte.OverallLength = 800
        self.PatternPalettte.FirstBlockLength = 100
        self.PatternPalettte.SecondaryBlockLength = 145
        self.PatternPalettte.ThirdBlockLength = 100
        self.PatternPalettte.FirstForkSpace = 227
        self.PatternPalettte.SecondForkSpace = 227
        self.PatternPalettte.PaletteMatchScore = 100.0
        self.Id = 0
        self.WrongPalletsCounter = 0
        #Initialization main infinite loop
        while not rospy.is_shutdown():
            try:
                distanceSub = rospy.Subscriber('PLC/read/distance', Int64, self.DistanceCallback)
                ScangridsDataSub = rospy.Subscriber('Forklift/Scangrids/DataOut', Scangrids, self.ScangridsCallback)
                startScanSub = rospy.Subscriber('Forklift/PalletData/StartScan', Bool, self.StartScanCallback)
                self.MainPalettePub = rospy.Publisher('Forklift/PalletData/MainPalette', Palette, queue_size=1, latch=True)
                
            except(rospy.ServiceException, rospy.ROSException) as e:
                rospy.logerr('Main loop error: %s' % e)
            rospy.loginfo_once('=========================================')
            rospy.loginfo_once('           INITIALIZATION PASSED')
            rospy.loginfo_once('=========================================')
            if self.StartScan:
                self.Scanner()
            self.Rate.sleep()
    #Additional functions
    def Colorize(self, text, color_code):
        return "\033[{}m{}\033[0m".format(color_code, text)
    def PrintGreen(self, message):
        print(self.Colorize(message, '92'))
    #Callbacks def area
    def StartScanCallback(self, msg):
        self.StartScan = msg.data
    def DistanceCallback(self, msg):
        self.DistanceNow = msg.data  
    def ScangridsCallback(self, msg):
        self.ScangridsDataIn = msg
        if self.SaveDistancesArea29:
            entry = {
                'Distance': self.DistanceNow,
                'Data': self.ScangridsDataIn.RightScanner.Range29
            }
            self.DistancesListArea29.append(entry)
        if self.SaveDistancesArea30:
            entry = {
                'Distance': self.DistanceNow,
                'Data': self.ScangridsDataIn.RightScanner.Range30
            }
            self.DistancesListArea30.append(entry)
        if self.SaveDistancesArea31:
            entry = {
                'Distance': self.DistanceNow,
                'Data': self.ScangridsDataIn.RightScanner.Range31
            }
            self.DistancesListArea31.append(entry)
        if self.SaveDistancesArea0:
            entry = {
                'Distance': self.DistanceNow,
                'Data': self.ScangridsDataIn.LeftScanner.Range0
            }
            self.DistancesListArea0.append(entry)   
        if self.SaveDistancesArea1:
            entry = {
                'Distance': self.DistanceNow,
                'Data': self.ScangridsDataIn.LeftScanner.Range1
            }
            self.DistancesListArea1.append(entry)  
        if self.SaveDistancesArea2:
            entry = {
                'Distance': self.DistanceNow,
                'Data': self.ScangridsDataIn.LeftScanner.Range2
            }
            self.DistancesListArea2.append(entry)
    def LenghtCalculator(self, distanceList, accuracy):
        sortedList = sorted(distanceList, key=lambda x: x['Data'])
        minDistance = 0.0
        maxDistance = 0.0
        if len(sortedList) >= 2:
            minimalDataValue = sortedList[0]['Data']
            acceptedValuesList = [item for item in sortedList if minimalDataValue <= item['Data'] <= minimalDataValue + accuracy]
            maxDistance = max([item['Distance'] for item in acceptedValuesList])
            minDistance = min([item['Distance'] for item in acceptedValuesList])
            distance = maxDistance - minDistance
        else:
            distance = -1
        return distance, minDistance, maxDistance, accuracy
    def PatternMatcher(self, pattern, data1, data2, data3):
        differencies = [(abs(pattern - data1), data1), (abs(pattern - data2), data2),(abs(pattern - data3), data3)]
        minimalDiff = min(differencies)
        if minimalDiff == differencies[0]:
            return data1
        elif minimalDiff == differencies[1]:
            return data2
        else:
            return data3
    def PatternMatcherV2(self, pattern, data1, data2, data3):
        differencies = [(abs(pattern - data1), data1), (abs(pattern - data2), data2),(abs(pattern - data3), data3)]
        minimalDiff = min(differencies)
        if minimalDiff == differencies[0]:
            return data1
        elif minimalDiff == differencies[1]:
            return data2
        else:
            return data3
    def MatchingScoreValidator(self):
        percentages = []
        counter = 0
        score = 0.0
        minimalScore = 100.0
        percentages.append(round(((self.MainPalette.OverallLength * 100) / 800), 2))
        percentages.append(round(((self.MainPalette.FirstBlockLength * 100) / 100), 2))
        percentages.append(round(((self.MainPalette.SecondaryBlockLength * 100) / 145), 2))
        percentages.append(round(((self.MainPalette.ThirdBlockLength * 100) / 100), 2))
        percentages.append(round(((self.MainPalette.FirstForkSpace * 100) / 227), 2))
        percentages.append(round(((self.MainPalette.SecondForkSpace * 100) / 227), 2))
        for item in percentages:
            if item > 100.0:
                item = 100 - ( item - 100)
            if item < minimalScore:
                minimalScore = item
                print(counter)
            score = score + item
            counter += 1
        self.MainPalette.PalleteMinimalMatchScore = minimalScore
        self.MainPalette.PaletteMatchScore = round((score / counter), 2)
    def CalculateMatchingScore(self, palette):
        percentages = []
        counter = 0
        score = 0.0
        minimalScore = 100.0
        percentages.append(round(((palette.OverallLength * 100) / self.PatternPalettte.OverallLength), 2))
        percentages.append(round(((palette.FirstBlockLength * 100) / self.PatternPalettte.FirstBlockLength), 2))
        percentages.append(round(((palette.SecondaryBlockLength * 100) / self.PatternPalettte.SecondaryBlockLength), 2))
        percentages.append(round(((palette.ThirdBlockLength * 100) / self.PatternPalettte.ThirdBlockLength), 2))
        percentages.append(round(((palette.FirstForkSpace * 100) / self.PatternPalettte.FirstForkSpace), 2))
        percentages.append(round(((palette.SecondForkSpace * 100) / self.PatternPalettte.SecondForkSpace), 2))
        for item in percentages:
            if item > 100.0:
                item = 100 - ( item - 100)
            if item < minimalScore:
                minimalScore = item
                print(counter)
            score = score + item
            counter += 1
        minimalScore = minimalScore
        overallScore = round((score / counter), 2)
        return overallScore, minimalScore
    def DimensionVerifier(self):
        if ((self.PatternPalettte.FirstBlockLength - 20) <= self.MainPalette.FirstBlockLength <= (self.PatternPalettte.FirstBlockLength + 20)):
            self.MainPalette.FirstBlockDetected = True
        if (((self.PatternPalettte.FirstBlockLength - 15) * 2) <= self.MainPalette.FirstBlockLength <= ((self.PatternPalettte.FirstBlockLength - 15) * 2)):
            self.MainPalette.FirstBlockLength = self.MainPalette.FirstBlockLength / 2
            if ((self.PatternPalettte.FirstBlockLength - 20) <= self.MainPalette.FirstBlockLength <= (self.PatternPalettte.FirstBlockLength + 20)):
                self.MainPalette.FirstBlockDetected = True
        if ((self.PatternPalettte.SecondaryBlockLength - 20) <= self.MainPalette.FirstBlockLength <= (self.PatternPalettte.SecondaryBlockLength + 20)):
            self.MainPalette.FirstBlockDetected = False
        if ((self.PatternPalettte.SecondaryBlockLength - 20) <= self.MainPalette.SecondaryBlockLength <= (self.PatternPalettte.SecondaryBlockLength + 35)):
            self.MainPalette.MiddleBlockDetected = True
        if ((self.PatternPalettte.ThirdBlockLength - 20) <= self.MainPalette.ThirdBlockLength <= (self.PatternPalettte.ThirdBlockLength + 20)):
            self.MainPalette.LastBlockDetected = True
        if (((self.PatternPalettte.ThirdBlockLength - 15) * 2) <= self.MainPalette.ThirdBlockLength <= ((self.PatternPalettte.ThirdBlockLength - 15) * 2)):
            self.MainPalette.FirstBlockLength = self.MainPalette.FirstBlockLength / 2
            if ((self.PatternPalettte.ThirdBlockLength - 20) <= self.MainPalette.ThirdBlockLength <= (self.PatternPalettte.ThirdBlockLength + 20)):
                self.MainPalette.LastBlockDetected = True
        if ((self.PatternPalettte.SecondaryBlockLength - 20) <= self.MainPalette.ThirdBlockLength <= (self.PatternPalettte.SecondaryBlockLength + 20)):
            self.MainPalette.LastBlockDetected = False
        if self.MainPalette.FirstBlockDetected and self.MainPalette.MiddleBlockDetected and self.MainPalette.LastBlockDetected:
            self.MainPalette.PaletteOk = True
        else:
            self.MainPalette.PaletteOk = False
        if self.MainPalette.OverallLength > 1000 or self.MainPalette.OverallLength < 600:
            self.MainPalette.PaletteOk = False
    def SinglePalette(self):
        self.MainPalettePub.publish(self.MainPalette)
        sleep(0.1)
        self.MainPalette = Palette()
        self.PaletteArea1 = Palette()
        self.PaletteArea2 = Palette()
        self.PaletteArea3 = Palette()
    def DataChooser(self):
        self.ScangridsDataIn.RightScanner.Range28
        self.MainPalette = Palette()
        self.MainPalette.OverallLength = self.PatternMatcher(self.PatternPalettte.OverallLength, self.PaletteArea1.OverallLength, self.PaletteArea2.OverallLength, self.PaletteArea3.OverallLength)
        self.MainPalette.FirstBlockLength = self.PatternMatcher(self.PatternPalettte.FirstBlockLength, self.PaletteArea1.FirstBlockLength, self.PaletteArea2.FirstBlockLength, self.PaletteArea3.FirstBlockLength)
        self.MainPalette.SecondaryBlockLength = self.PatternMatcher(self.PatternPalettte.SecondaryBlockLength, self.PaletteArea1.SecondaryBlockLength, self.PaletteArea2.SecondaryBlockLength, self.PaletteArea3.SecondaryBlockLength)
        self.MainPalette.ThirdBlockLength = self.PatternMatcher(self.PatternPalettte.ThirdBlockLength, self.PaletteArea1.ThirdBlockLength, self.PaletteArea2.ThirdBlockLength, self.PaletteArea3.ThirdBlockLength)
        self.MainPalette.FirstForkSpace = self.PatternMatcher(self.PatternPalettte.FirstForkSpace, self.PaletteArea1.FirstForkSpace, self.PaletteArea2.FirstForkSpace, self.PaletteArea3.FirstForkSpace)
        self.MainPalette.SecondForkSpace = self.PatternMatcher(self.PatternPalettte.SecondForkSpace, self.PaletteArea1.SecondForkSpace, self.PaletteArea2.SecondForkSpace, self.PaletteArea3.SecondForkSpace)
        self.MatchingScoreValidator()
        self.DimensionVerifier()
        self.MainPalette.Id = self.Id
        self.Id += 1
        if self.MainPalette.PaletteOk:
            rospy.logwarn('================================================================')
            rospy.logwarn('                 PRINTING Area1 DATA')
            rospy.logwarn(self.PaletteArea1)
            rospy.logwarn('================================================================')
            rospy.logwarn('                 PRINTING Area2 DATA')
            rospy.logwarn(self.PaletteArea2)
            rospy.logwarn('================================================================')
            rospy.logwarn('                 PRINTING Area3 DATA')
            rospy.logwarn(self.PaletteArea3)
            self.PrintGreen('================================================================')
            self.PrintGreen('                 PRINTING BEST MATCHING DATA')
            self.PrintGreen('================================================================')
            rospy.loginfo(self.MainPalette)
            if self.StackPallets and not self.SinglePaletteMode:
                self.AppendPallet()
            elif not self.StackPallets and self.SinglePaletteMode:
                self.SinglePalette()
            elif self.StackPallets and self.SinglePaletteMode:
                rospy.logerr(' Choose only one mode of finishing the scanning!')
            elif not self.StackPallets and not self.SinglePaletteMode:
                rospy.logerr("Choose mode of finishing the scan: StackPallets or single palette mode")
        else:
            rospy.logerr('================================================================')
            rospy.logerr('                 PRINTING BEST MATCHING DATA')
            rospy.logerr('================================================================')
            rospy.loginfo(self.MainPalette)
            self.MainPalette = Palette()
            self.WrongPalletsCounter += 1
        rospy.logwarn(self.WrongPalletsCounter)
    def PaletteChooser(self):
        self.MainPalette = Palette()
        if self.PaletteSearchSide == 1:
            score1 = self.CalculateMatchingScore(self.PaletteArea1)
            score2 = self.CalculateMatchingScore(self.PaletteArea2)
            score3 = self.CalculateMatchingScore(self.PaletteArea3)
            self.PaletteArea1.PaletteMatchScore = score1[0]
            self.PaletteArea1.PalleteMinimalMatchScore = score1[1]
            self.PaletteArea2.PaletteMatchScore = score2[0]
            self.PaletteArea2.PalleteMinimalMatchScore = score2[1]
            self.PaletteArea3.PaletteMatchScore = score3[0]
            self.PaletteArea3.PalleteMinimalMatchScore = score3[1]
            self.PaletteArea1.BeamId = 1
            self.PaletteArea2.BeamId = 2
            self.PaletteArea3.BeamId = 3
            unsortedList = []
            unsortedList.append(self.PaletteArea1)
            unsortedList.append(self.PaletteArea2)
            unsortedList.append(self.PaletteArea3)
            sortedList = sorted(unsortedList, key=lambda x: x.PaletteMatchScore, reverse=True)
            for i in range(0, len(sortedList)):
                self.MainPalette = sortedList[i]
                self.DimensionVerifier()
                if self.MainPalette.PaletteOk:
                    self.MainPalette
                    break
            self.MainPalette.Id = self.Id
            self.Id += 1
            if self.MainPalette.PaletteOk:
                rospy.logwarn('================================================================')
                rospy.logwarn('                 PRINTING Area1 DATA')
                rospy.logwarn(self.PaletteArea1)
                rospy.logwarn('================================================================')
                rospy.logwarn('                 PRINTING Area2 DATA')
                rospy.logwarn(self.PaletteArea2)
                rospy.logwarn('================================================================')
                rospy.logwarn('                 PRINTING Area3 DATA')
                rospy.logwarn(self.PaletteArea3)
                self.PrintGreen('================================================================')
                self.PrintGreen('                 PRINTING BEST MATCHING DATA')
                self.PrintGreen('================================================================')
                rospy.loginfo(self.MainPalette)
                if self.StackPallets and not self.SinglePaletteMode:
                    self.AppendPallet()
                elif not self.StackPallets and self.SinglePaletteMode:
                    self.SinglePalette()
                elif self.StackPallets and self.SinglePaletteMode:
                    rospy.logerr(' Choose only one mode of finishing the scanning!')
                elif not self.StackPallets and not self.SinglePaletteMode:
                    rospy.logerr("Choose mode of finishing the scan: StackPallets or single palette mode")
            else:
                rospy.logerr('================================================================')
                rospy.logerr('                 PRINTING BEST MATCHING DATA')
                rospy.logerr('================================================================')
                rospy.loginfo(self.MainPalette)
                self.MainPalette = Palette()
                self.WrongPalletsCounter += 1
            rospy.logwarn(self.WrongPalletsCounter)              
    def AppendPallet(self):
        self.PalletesList.append(self.MainPalette)
        self.MainPalettePub.publish(self.PalletesList[len(self.PalletesList) - 1])
        sleep(0.1)
        self.MainPalette = Palette()
        self.PaletteArea1 = Palette()
        self.PaletteArea2 = Palette()
        self.PaletteArea3 = Palette()
        # self.MainPalettePub.publish(self.MainPalette)
    #Main program 
    def Scanner(self):
        if not self.MainPalette.PaletteOk:
            if self.PaletteSearchSide == 1:
                area1 = Palette()
                area2 = Palette()
                area3 = Palette()
                paletteDetectionDistance = self.BasePaletteExpectedDistance
                searchDistanceLimiter = 0
                searchDistanceLimiterSaved = False
                while True:
                    rospy.loginfo_once('Scanner ready, waiting for first edge...')
                    if self.ScangridsDataIn.LeftScanner != None:
                        self.SearchRange0 = self.ScangridsDataIn.LeftScanner.Range0
                        self.SearchRange1 = self.ScangridsDataIn.LeftScanner.Range1
                        self.SearchRange2 = self.ScangridsDataIn.LeftScanner.Range2       
                    #First area search
                    if self.SearchRange0 <= paletteDetectionDistance and not self.SearchRange0 == 0:
                        if area1.StartDistance == 0:
                            
                            area1.FirstBlockDistance = self.SearchRange0
                            self.DistancesListArea0 = []
                            self.SaveDistancesArea0 = True
                            if not searchDistanceLimiterSaved:
                                searchDistanceLimiter = self.DistanceNow
                                area1.StartDistance = self.DistanceNow
                                searchDistanceLimiterSaved = True
                                rospy.loginfo('Search distance limiter saved at area 1!')
                    if not area1.FirstBlockDetected:
                        if self.SearchRange0 > (paletteDetectionDistance + self.ReadingSpike) and area1.StartDistance != 0:
                            self.SaveDistancesArea0 = False
                            scanData = self.LenghtCalculator(self.DistancesListArea0, 10)
                            area1.FirstBlockLength = scanData[0]
                            area1.StartDistance = scanData[1]
                            self.DistancesListArea0.clear()
                            area1.FirstBlockDetected = True
                            self.SaveDistancesArea0 = True
                    if area1.FirstBlockDetected and not area1.MiddleBlockDetected:
                        if self.SearchRange0 <= paletteDetectionDistance and area1.FirstForkSpace == 0:
                            area1.FirstForkSpace = 1
                            area1.SecondBlockDistance = self.SearchRange0
                        if area1.FirstForkSpace != 0 and self.SearchRange0 > (paletteDetectionDistance + self.ReadingSpike):
                            self.SaveDistancesArea0 = False
                            scanData = self.LenghtCalculator(self.DistancesListArea0, 10)
                            area1.SecondaryBlockLength = scanData[0]
                            self.DistancesListArea0.clear()
                            self.SaveDistancesArea0 = True
                            area1.MiddleBlockDetected = True
                    if area1.FirstBlockDetected and area1.MiddleBlockDetected and not area1.LastBlockDetected:
                        if self.SearchRange0 <= paletteDetectionDistance and area1.SecondForkSpace == 0:
                            area1.SecondForkSpace = 1
                            area1.ThirdBlockDistance = self.SearchRange0
                        if area1.SecondForkSpace != 0 and self.SearchRange0 > (paletteDetectionDistance + self.ReadingSpike):
                            self.SaveDistancesArea0 = False
                            scanData = self.LenghtCalculator(self.DistancesListArea0, 10)
                            area1.ThirdBlockLength = scanData[0]
                            area1.EndDistance = scanData[2]
                            self.DistancesListArea0.clear()
                            area1.LastBlockDetected = True
                    if area1.FirstBlockDetected and area1.MiddleBlockDetected and area1.LastBlockDetected:
                        area1.OverallLength = area1.EndDistance - area1.StartDistance
                        area1.FirstForkSpace = (area1.OverallLength - (area1.FirstBlockLength + area1.SecondaryBlockLength + area1.ThirdBlockLength)) / 2
                        area1.SecondForkSpace = area1.FirstForkSpace
                        area1.PaletteOk = True
                    # Second area search
                    if self.SearchRange1 <= paletteDetectionDistance and not self.SearchRange1 == 0:
                        if area2.StartDistance == 0:
                            area2.StartDistance = self.DistanceNow
                            area2.FirstBlockDistance = self.SearchRange1
                            self.DistancesListArea1 = []
                            self.SaveDistancesArea1 = True
                            if not searchDistanceLimiterSaved:
                                searchDistanceLimiter = self.DistanceNow
                                # rospy.loginfo(self.DistanceNow)
                                searchDistanceLimiterSaved = True
                                rospy.loginfo('Search distance limiter saved at area 2!')
                    if not area2.FirstBlockDetected and area2.StartDistance != 0:
                        if self.SearchRange1 > (paletteDetectionDistance + self.ReadingSpike):
                            self.SaveDistancesArea1 = False
                            scanData2 = self.LenghtCalculator(self.DistancesListArea1, 10)
                            if scanData2[0] >= 120:
                                scanData2tmp = self.LenghtCalculator(self.DistancesListArea1, 5)
                            elif scanData2[0] <= 80:
                                scanData2tmp = self.LenghtCalculator(self.DistancesListArea1, 15)
                            rospy.logwarn(f'Strefa 2 - pierwsza kostka: {scanData2}')
                            area2.FirstBlockLength = scanData2[0]
                            area2.StartDistance = scanData2[1]
                            # rospy.loginfo(scanData2)
                            # rospy.loginfo(self.DistanceNow)
                            self.DistancesListArea1.clear()
                            area2.FirstBlockDetected = True
                            self.SaveDistancesArea1 = True
                    if area2.FirstBlockDetected and not area2.MiddleBlockDetected:
                        if self.SearchRange1 <= paletteDetectionDistance and area2.FirstForkSpace == 0:
                            area2.FirstForkSpace = 1
                            # rospy.loginfo_once('Saved forkSpace 1 at area 2')
                            # rospy.loginfo(self.DistanceNow)
                            area2.SecondBlockDistance = self.SearchRange1
                        if area2.FirstForkSpace != 0 and self.SearchRange1 > (paletteDetectionDistance + self.ReadingSpike):
                            self.SaveDistancesArea1 = False
                            scanData2 = self.LenghtCalculator(self.DistancesListArea1, 10)
                            if scanData2[0] < 125:
                                scanData2 = self.LenghtCalculator(self.DistancesListArea1, 15)
                            if scanData2[0] > 165:
                                scanData2 = self.LenghtCalculator(self.DistancesListArea1, 5)
                            rospy.logwarn(f'Strefa 2 - druga kostka: {scanData2}')
                            # rospy.loginfo(scanData2)
                            area2.SecondaryBlockLength = scanData2[0]
                            # rospy.loginfo(self.DistanceNow)
                            self.DistancesListArea1.clear()
                            # rospy.loginfo_once('Saved block 2 at area 2')
                            self.SaveDistancesArea1 = True
                            area2.MiddleBlockDetected = True
                    if area2.FirstBlockDetected and area2.MiddleBlockDetected and not area2.LastBlockDetected:
                        if self.SearchRange1 <= paletteDetectionDistance and area2.SecondForkSpace == 0:
                            area2.SecondForkSpace = 1
                            area2.ThirdBlockDistance = self.SearchRange1
                            # rospy.loginfo(self.DistanceNow)
                        if area2.SecondForkSpace != 0 and self.SearchRange1 > (paletteDetectionDistance + self.ReadingSpike):
                            self.SaveDistancesArea1 = False
                            scanData2 = self.LenghtCalculator(self.DistancesListArea1, 10)
                            if scanData2[0] >= 120:
                                scanData2 = self.LenghtCalculator(self.DistancesListArea1, 5)
                            elif scanData2[0] <= 80:
                                scanData2 = self.LenghtCalculator(self.DistancesListArea1, 15)

                            area2.ThirdBlockLength = scanData2[0]
                            rospy.logwarn(f'Strefa 2 - trzecia kostka: {area2.ThirdBlockLength}')
                            area2.EndDistance = scanData2[2]
                            area2.LastBlockDetected = True
                            # rospy.loginfo(self.DistanceNow)
                            # rospy.loginfo_once('Saved block 3 at area 2')
                            self.DistancesListArea1.clear()
                    if area2.FirstBlockDetected and area2.MiddleBlockDetected and area2.LastBlockDetected:
                        area2.OverallLength = area2.EndDistance - area2.StartDistance
                        area2.FirstForkSpace = (area2.OverallLength - (area2.FirstBlockLength + area2.SecondaryBlockLength + area2.ThirdBlockLength)) / 2
                        area2.SecondForkSpace = area2.FirstForkSpace
                        area2.PaletteOk = True
                    # Third area search
                    if self.SearchRange2 <= paletteDetectionDistance and not self.SearchRange2 == 0:
                        if area3.StartDistance == 0:
                            area3.StartDistance = self.DistanceNow
                            area3.FirstBlockDistance = self.SearchRange2
                            self.DistancesListArea2 = []
                            self.SaveDistancesArea2 = True
                            if not searchDistanceLimiterSaved:
                                searchDistanceLimiter = self.DistanceNow
                                searchDistanceLimiterSaved = True
                                # rospy.loginfo('Search distance limiter saved at area 2!')
                    if not area3.FirstBlockDetected:
                        if self.SearchRange2 > (paletteDetectionDistance + self.ReadingSpike) and area3.StartDistance != 0:
                            self.SaveDistancesArea2 = False
                            scanData3 = self.LenghtCalculator(self.DistancesListArea2, 10)
                            if scanData3[0] < 80:
                                scanData3 = self.LenghtCalculator(self.DistancesListArea1, 15)
                            elif scanData3[0] > 125:
                                scanData3 = self.LenghtCalculator(self.DistancesListArea1, 5)
                            rospy.logwarn(f'Strefa 3 - pierwsza kostka: {scanData3}')
                            area3.FirstBlockLength = scanData3[0]
                            area3.StartDistance = scanData3[1]
                            self.DistancesListArea2.clear()
                            area3.FirstBlockDetected = True
                            self.SaveDistancesArea2 = True
                    if area3.FirstBlockDetected and not area3.MiddleBlockDetected:
                        if self.SearchRange2 <= paletteDetectionDistance and area3.FirstForkSpace == 0:
                            area3.FirstForkSpace = 1
                            area3.SecondBlockDistance = self.SearchRange2
                        if area3.FirstForkSpace != 0 and self.SearchRange2 > (paletteDetectionDistance + self.ReadingSpike):
                            self.SaveDistancesArea2 = False
                            scanData3 = self.LenghtCalculator(self.DistancesListArea2, 10)
                            if scanData3[0] < 125:
                                scanData3 = self.LenghtCalculator(self.DistancesListArea1, 15)
                            
                            elif scanData3[0] > 165:
                                scanData3 = self.LenghtCalculator(self.DistancesListArea1, 5)
                            rospy.logwarn(f'Strefa 3 - druga kostka: {scanData3}')
                            area3.SecondaryBlockLength = scanData3[0]
                            self.DistancesListArea2.clear()
                            self.SaveDistancesArea2 = True
                            area3.MiddleBlockDetected = True
                    if area3.FirstBlockDetected and area3.MiddleBlockDetected and not area3.LastBlockDetected:
                        if self.SearchRange2 <= paletteDetectionDistance and area3.SecondForkSpace == 0:
                            area3.SecondForkSpace = 1
                            area3.ThirdBlockDistance = self.SearchRange2
                        if area3.SecondForkSpace != 0 and self.SearchRange2 > (paletteDetectionDistance + self.ReadingSpike):
                            self.SaveDistancesArea2 = False
                            scanData3 = self.LenghtCalculator(self.DistancesListArea2, 10)
                            if scanData3[0] < 80:
                                scanData3 = self.LenghtCalculator(self.DistancesListArea1, 15)
                            if scanData3[0] > 120:
                                scanData3 = self.LenghtCalculator(self.DistancesListArea1, 5)
                            area3.ThirdBlockLength = scanData3[0]
                            
                            rospy.logwarn(f'Strefa 3 - trzecia kostka: {scanData3}')
                            area3.ThirdBlockLength = scanData3[0]
                            area3.EndDistance = scanData3[2]
                            area3.LastBlockDetected = True
                            self.DistancesListArea2.clear()
                    if area3.FirstBlockDetected and area3.MiddleBlockDetected and area3.LastBlockDetected:
                        area3.OverallLength = area3.EndDistance - area3.StartDistance
                        area3.FirstForkSpace = (area3.OverallLength - (area3.FirstBlockLength + area3.SecondaryBlockLength + area3.ThirdBlockLength)) / 2
                        area3.SecondForkSpace = area3.FirstForkSpace
                        area3.PaletteOk = True
                    if (area1.PaletteOk and area2.PaletteOk) or (area2.PaletteOk and area3.PaletteOk) or (area1.PaletteOk and area3.PaletteOk):
                        self.PaletteArea1 = area1
                        self.PaletteArea2 = area2
                        self.PaletteArea3 = area3
                        
                    
                        self.PaletteChooser()
                        area1 = Palette()
                        area2 = Palette()
                        area3 = Palette()
                        
                            
if __name__ == '__main__':
    try:
        rospy.init_node('PalletScannerNode')
        palletScanner = PalletScanner()
        rospy.loginfo_once('=========================================')
        rospy.loginfo_once('                   MAIN                  ')
        rospy.loginfo_once('=========================================')
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr('Main initialization failed: %s' % e)