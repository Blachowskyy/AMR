#!/usr/bin/env python3

from time import sleep
import rospy 
import os
import math
import datetime as DT
from std_msgs.msg import Bool, Float32, Int64, Int64MultiArray
from robot_dhi_1.msg import LogMessages, Distance, Palette, ScangridSteering, Scangrids

class MagazineDriver:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        #Custom data
        self.Rate = rospy.Rate(30)
        self.DistanceToPublish = Distance()
        self.LastDistanceToPublish = Distance()
        self.ScannedPalette = Palette()
        self.ScangridSteering = ScangridSteering()
        self.ScangridsDataIn = Scangrids()
        self.ScangridsDataOut = Scangrids()
        #Int data
        self.CurtisPower = 0
        self.DistanceNow = 0
        self.SearchSide = 1 # 1 po lewej, 2 po prawej
        self.ScanDistance = 0
        #Int64MultiArray data
        self.ScangridLeftData = Int64MultiArray()
        self.ScangridRightData = Int64MultiArray()
        #Float data
        self.ServoAngle = 0.0
        self.ServoAngleNow = 0.0
        self.ForkliftTurningRadiusForksUp = 1100.0
        self.ForkliftTurningRadiusForksDown = 1200.0
        self.CalculatedDistance = 0.0
        self.ForkliftLenght = 1250.00
        self.CalculatedDistanceUnderThePallet = 0.0
        self.GoOutFirstDistance = 0.0
        self.GoOutSecondDistance = 0.0
        self.GoOutFirstServoAngle = 0.0
        self.GoOutSecondServoAngle = 0.0
        self.OffsetToRotationCenter = 0.0 # UZUPELNIC
        self.ScangridMountingPointOffset = 140.0
        self.ForkWidth = 160.0
        self.BeamsAngle = 4.6875
        #Bool data
        self.StartDrive = False
        self.CancelDrive = False
        self.ResetDistance = False
        self.EnableDrive = False
        self.ForksHeightLimiterStatus = False
        self.NewPaletteBlockade = False
        self.PositionReached = False
        self.GoToMiddlePoint = False
        self.GoInFront = False
        self.GoUnderPalette = False
        self.PaletteScanRequest = False
        self.GoOut = False
        self.EnablePaletteScan = False
        self.PaletteSearchRepeat = False
        self.PaletteLocalized = False
        self.InMiddlePoint = False
        self.InFrontOfPalette = False
        self.UnderPalette = False
        #Devmode
        self.DevMode = False
        self.DevModeOption = 0
        while not rospy.is_shutdown():
            try:
            #Subscribers
                paletteDataSub = rospy.Subscriber('Forklift/PalletData/MainPalette', Palette, self.MainPaletteCallback)
                positionReachedSub = rospy.Subscriber('Forklift/DistanceDrive/PositionReached', Bool, self.PositionReachedCallback)
                forksHeightLimiterSub = rospy.Subscriber('PLC/read/forks_height_limiter', Int64, self.ForksHeightLimiterCallback)
                currentDistanceSub = rospy.Subscriber('PLC/read/distance', Int64, self.CurrentDistanceCallback)
                servoAngleNowSub = rospy.Subscriber('Forklift/drive/current_servo_angle', Float32, self.CurrentServoAngleCallback)
                enableGoToMiddleSub = rospy.Subscriber('Forklift/PalletData/steering/goToMiddlePoint', Bool, self.GoToMiddlePointCallback)
                enableGoInFrontSub = rospy.Subscriber('Forklift/PalletData/steering/goInFront', Bool, self.GoInFrontCallback)
                enableGoUnderPaletteSub = rospy.Subscriber('Forklift/PalletData/steering/goUnderPalette', Bool, self.GoUnderPaletteCallback)
                paletteScanRequestSub = rospy.Subscriber('Forklift/PalletData/steering/scanRequest', Bool, self.PaletteScanRequestCallback)
                scangrdisDataInSub = rospy.Subscriber('Forklift/Scangrids/DataOut', Scangrids, self.ScangridsDataOutCallback)
                goOutSub = rospy.Subscriber('Forklift/PalletData/steering/goOut', Bool, self.GoOutCallback)
                enableDevModeSub = rospy.Subscriber('Forklift/DevMode/MagazineDriver/Enable', Bool, self.EnableDevModeCallback)
                devModeOptionSub = rospy.Subscriber('Forklift/DevMode/MagazineDtiver/Option', Int64, self.DevModeOptionCallback)
                #Publishers
                self.distancePub = rospy.Publisher('Forklift/DistanceNavigator/DistanceV2', Distance, queue_size=1, latch=True)
                self.curtisPowerPub = rospy.Publisher('Forklift/DistanceNavigator/PWM', Int64, queue_size=1, latch=True)
                self.servoAnglePub = rospy.Publisher('Forklift/DistanceNavigator/Angle', Float32, queue_size=1, latch=True)
                self.startDrivePub = rospy.Publisher('Forklift/DistanceNavigator/Start', Bool, queue_size=1, latch=True)
                self.resetPub = rospy.Publisher('Forklift/DistanceNavigator/Reset', Bool, queue_size=1, latch=True)
                self.cancelDrivePub = rospy.Publisher('Forklift/DistanceNavigator/Cancel', Bool, queue_size=1, latch=True)
                self.enablePub = rospy.Publisher('Forklift/DistanceNavigator/Enable', Bool, queue_size=1, latch=True)
                self.enableScanPub = rospy.Publisher('Forklift/PalletData/StartScan', Bool, queue_size=1, latch=True)
                self.ScangridsDataOutPub = rospy.Publisher('Forklift/Scangrids/DataIn', ScangridSteering, queue_size=1, latch=True)        
            except(rospy.ServiceException, rospy.ROSException) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
            os.system('clear') 
            if not self.DevMode:
                self.WorkSelector()
            if self.DevMode:
                if self.DevModeOption == 1:
                    if self.ScannedPalette.PaletteOk:
                        result = self.GetOffsetToMiddlePoint(self.ScannedPalette.SecondBlockDistance)
                        print(result)   
                if self.DevModeOption == 2:
                    if self.ScannedPalette.PaletteOk:
                        result = self.CalculateRoadToMiddlePoint()
                        print(result)
                if self.DevModeOption == 3:
                    if self.ScannedPalette.PaletteOk:
                        result = self.CalculateRoadToFrontOfPallet()
                        print(result)
                if self.DevModeOption == 4:
                    print(f'selected option: {self.DevModeOption}')
                    result = self.CalculateAverageReadingsFromScangrids()
                    print(result)
            self.Rate.sleep()
            print('+++++++++++++++++++++++++MAIN LOOP+++++++++++++++++++++++++++++')
      
               
    #Other functions
    def Colorize(self, text, color_code):
        return "\033[{}m{}\033[0m".format(color_code, text)
    def PrintGreen(self, message):
        print(self.Colorize(message, '92'))
    #Callback's region
    def EnableDevModeCallback(self, msg):
        self.DevMode = msg.data
    def DevModeOptionCallback(self, msg):
        self.DevModeOption = msg.data
    def GoOutCallback(self, msg):
        self.GoOut = msg.data
    def ScangridsDataOutCallback(self, msg):
        self.ScangridsDataIn = msg
    def PaletteScanRequestCallback(self, msg):
        self.PaletteScanRequest = msg.data
    def MainPaletteCallback(self, msg):
        # data = Palette()
        # data = msg
        # if data.Id != self.ScannedPalette.Id and not self.NewPaletteBlockade:
        #     self.ScannedPalette = data
        #     self.NewPaletteBlockade = True
        self.ScannedPalette = msg
    def PositionReachedCallback(self, msg):
        self.PositionReached = msg.data
    def ForksHeightLimiterCallback(self, msg):
        data = msg.data
        if data == 0:
            self.ForksHeightLimiterStatus = False
        elif data == 1:
            self.ForksHeightLimiterStatus = True
        else:
            rospy.logerr('Wrong fork height limiter data!')
    def CurrentDistanceCallback(self, msg):
        self.DistanceNow = msg.data
    def CurrentServoAngleCallback(self, msg):
        self.ServoAngleNow = msg.data
    def GoToMiddlePointCallback(self, msg):
        self.GoToMiddlePoint = msg.data
    def GoInFrontCallback(self, msg):
        self.GoInFront = msg.data
    def GoUnderPaletteCallback(self, msg):
        self.GoUnderPalette = msg.data
    #Calculate data logic
    def CalculateAverageReadingsFromScangrids(self):
        self.ScangridsDataOut.Steering.ActivateAllZones = True
        self.ScangridsDataOut.Steering.ActivateLeftPaletteDetection = False
        self.ScangridsDataOut.Steering.ActivateRightPaletteDetection = False
        sleep(0.2)
        rangesList = []
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range0)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range1)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range2)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range3)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range4)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range5)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range6)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range7)
        # rangesList.append(self.ScangridsDataIn.LeftScanner.Range8)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range9)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range10)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range11)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range12)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range13)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range14)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range15)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range16)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range17)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range18)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range19)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range20)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range21)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range22)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range23)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range24)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range25)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range26)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range27)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range28)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range29)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range30)
        rangesList.append(self.ScangridsDataIn.LeftScanner.Range31)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range0)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range1)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range2)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range3)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range4)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range5)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range6)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range7)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range8)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range9)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range10)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range11)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range12)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range13)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range14)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range15)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range16)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range17)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range18)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range19)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range20)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range21)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range22)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range23)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range24)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range25)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range26)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range27)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range28)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range29)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range30)
        rangesList.append(self.ScangridsDataIn.RightScanner.Range31)
        # print(rangesList)

        sortedRangesList = sorted(rangesList)
        minimalValue = min(sortedRangesList)
        acceptedValuesList = [item for item in sortedRangesList if minimalValue <= item <= minimalValue + 10]
        averageReadings = sum(acceptedValuesList) / len(acceptedValuesList)
        return averageReadings
    def GetOffsetToMiddlePoint(self, scanDistance):
        result = 0.0
        result = round(((scanDistance + (self.ForkWidth / 2))*(2 * (math.sin(math.radians(self.BeamsAngle)))) / (2 * (math.sin(math.radians(180.0 - (90.0 + self.BeamsAngle)))))), 0)
        
        rospy.loginfo(f'RESULT: {result}')
        
        if self.ScannedPalette.BeamId == 1 or self.ScannedPalette.BeamId == 31:
            return -result
        if self.ScannedPalette.BeamId == 2 or self.ScannedPalette.BeamId == 30:
            return 0
        if self.ScannedPalette.BeamId == 3 or self.ScannedPalette.BeamId == 29:
            return round(result, 0)
    def GetAverageScanDistance(self):
        result = (self.ScannedPalette.FirstBlockDistance + self.ScannedPalette.SecondBlockDistance + self.ScannedPalette.ThirdBlockDistance) / 3
        return result
    def CalculateRoadToMiddlePoint(self):
        averageScanDistance = self.GetAverageScanDistance()
        middleScanDistance = self.ScannedPalette.SecondBlockDistance
        beamOffset = self.GetOffsetToMiddlePoint(averageScanDistance)
        distanceToDrive = 0
        rospy.logwarn(f'Distance now: {self.DistanceNow}')
        rospy.logwarn(f'self.ScannedPalette.EndDistance: {self.ScannedPalette.EndDistance}')
        rospy.logwarn(f'ScannedPalette.OverallLength: {self.ScannedPalette.OverallLength}')
        rospy.logwarn(f'ScangridMountingPointOffset: {self.ScangridMountingPointOffset}')
        rospy.logwarn(f'beamOffset: {beamOffset}')
        distanceToDrive = int(round(self.DistanceNow - (self.DistanceNow - (self.DistanceNow - self.ScannedPalette.EndDistance) - (self.ScannedPalette.OverallLength / 2)) + self.ScangridMountingPointOffset + (beamOffset)))
        return distanceToDrive
    def CalculateRoadToFrontOfPallet(self):
        if self.SearchSide == 1:
            self.ServoAngle = -90.00
            self.PrintGreen(f'Servo angle setted at: {self.ServoAngle} degrees')
        elif self.SearchSide == 2:
            self.ServoAngle = 90.00
            self.PrintGreen(f'Servo angle setted at: {self.ServoAngle} degrees')
        else:
            p = math.atan2()
            rospy.logerr('Wrong search side in calculation to front of palette module')
        r = 0.0
        if self.ForksHeightLimiterStatus:
            r = self.ForkliftTurningRadiusForksDown
            self.PrintGreen(f'Turning radius  setted at: {r} mm')
        elif not self.ForksHeightLimiterStatus:
            r = self.ForkliftTurningRadiusForksUp
            self.PrintGreen(f'Turning radius  setted at: {r} mm')
        distanceToDrive = (((math.pi * r) / 2) + (self.ScannedPalette.FirstBlockDistance - self.ScannedPalette.ThirdBlockDistance)) - self.OffsetToRotationCenter
        if self.LastDistanceToPublish.Distance >= 0:
            distanceToDrive = int(round(distanceToDrive))
        elif self.LastDistanceToPublish.Distance < 0:
            distanceToDrive = int(round(-distanceToDrive))
        self.GoOutSecondDistance = -distanceToDrive
        self.GoOutFirstServoAngle = self.ServoAngle
        return distanceToDrive
    def CalculateRoadUnderPalette(self):
        distanceToPallet = self.CalculateAverageReadingsFromScangrids()
        self.CalculatedDistanceUnderThePallet = distanceToPallet + self.ForkliftLenght
        self.GoOutFirstDistance = -self.CalculatedDistanceUnderThePallet
    def CalculateScanDistance(self):
        #Tu w przyszlosci bedzie obliczanie dystansu skanowania
        scanDistance = 1450
        return scanDistance
    def GetSearchSide(self):
        #Tu w przyszlosci bedzie algorytm okreslajacy strone skanowania
        searchSide = 1
        return searchSide
    # #Function modules
    def EmergencyStop(self):
        rospy.logerr('Emergency stop activated!')
        self.CurtisPower = 0
        self.ServoAngle = 0
        self.StartDrive = False
        self.CancelDrive = True
        self.startDrivePub.publish(self.StartDrive)
        self.cancelDrivePub.publish(self.CancelDrive)
        self.curtisPowerPub.publish(self.CurtisPower)
        self.servoAnglePub.publish(self.ServoAngle)
    def CollisionAvoidanceModule(self):
        minimalLeftScangridDistance = 120
        minimalRightScangridDistance = 120
        while not self.PositionReached:
            if self.ScangridsDataIn.LeftScanner.Range16 < minimalLeftScangridDistance or self.ScangridsDataIn.LeftScanner.Range17 < minimalLeftScangridDistance:
                rospy.logerr('Left scangrid engaging e-stop')
                self.EmergencyStop()
                break
            if self.ScangridsDataIn.RightScanner.Range13 < minimalRightScangridDistance or self.ScangridsDataIn.RightScanner.Range12 < minimalRightScangridDistance:
                rospy.logerr('right scangrid engaging e-stop')
                self.EmergencyStop()
                break
            
    def SearchPalette(self):
        scanStatus = False
        self.SearchSide = self.GetSearchSide()
        self.ScanDistance = self.CalculateScanDistance()
        if self.SearchSide == 1 or self.SearchSide == 2:
            if self.SearchSide == 1:
                self.PrintGreen('================================================================')
                self.PrintGreen('                 Search Side: LEFT')
                self.PrintGreen('================================================================')
                self.PrintGreen('          Activating required Scangrid ranges')
                self.ScangridsDataOut.Steering.ActivateAllZones = False
                self.ScangridsDataOut.Steering.ActivateLeftPaletteDetection = True
                self.ScangridsDataOut.Steering.ActivateRightPaletteDetection = False
                self.ScangridsDataOutPub.publish(self.ScangridsDataOutPub)
                sleep(0.1)
            if self.SearchSide == 1:
                self.PrintGreen('================================================================')
                self.PrintGreen('                 Search Side: RIGHT')
                self.PrintGreen('================================================================')
                self.ScangridsDataOut.Steering.ActivateAllZones = False
                self.ScangridsDataOut.Steering.ActivateLeftPaletteDetection = False
                self.ScangridsDataOut.Steering.ActivateRightPaletteDetection = True
                self.ScangridsDataOutPub.publish(self.ScangridsDataOutPub)
                sleep(0.1)
        else:
            rospy.logerr(f'Wrong search side calculation ( should be 1 or 2): {self.SearchSide} mm ')
            self.SearchSide = 0
        if self.ScanDistance > 600 or self.ScanDistance < -600:
            self.PrintGreen(f'Scan distance ok: {self.ScanDistance}')
            self.DistanceToPublish.Id = self.LastDistanceToPublish.Id + 1
            self.DistanceToPublish.Distance = self.ScanDistance
            self.distancePub.publish(self.DistanceToPublish)
            self.LastDistanceToPublish = self.DistanceToPublish
        else:
            rospy.logerr(f'Wrong scan distance, shold be above 600mm or below -600mm. Calculated value: {self.ScanDistance} mm')
            self.ScanDistance = 0
        if self.ScanDistance !=0 and self.SearchSide != 0:
            self.EnablePaletteScan = True
            self.enableScanPub.publish(self.EnablePaletteScan)
            sleep(0.1)
            self.EnableDrive = True
            self.CancelDrive = False
            self.enablePub.publish(self.EnableDrive)
            self.cancelDrivePub.publish(self.CancelDrive)
            while not self.ScannedPalette.PaletteOk:
                distanceLimitError = self.DistanceNow
                if self.ScanDistance < (self.DistanceNow - distanceLimitError):
                    self.EnableDrive = False
                    self.CancelDrive = True
                    self.enablePub.publish(self.EnableDrive)
                    self.cancelDrivePub.publish(self.CancelDrive)
                    rospy.logerr('Search distance exceeded and palette not found!')
                    break
                if self.ScannedPalette.PaletteOk:
                    self.EnableDrive = False
                    self.CancelDrive = True
                    self.enablePub.publish(self.EnableDrive)
                    self.cancelDrivePub.publish(self.CancelDrive)
                    self.PrintGreen('================================================================')
                    self.PrintGreen('                 PALETTE FOUND! DATA:')
                    self.PrintGreen(self.ScannedPalette)
                    self.PrintGreen('================================================================')
                    break
            if self.ScannedPalette.PaletteOk:
                self.PaletteScanRequest = False
                self.PaletteSearchRepeat = False
                scanStatus = True
            else:
                self.PaletteSearchRepeat = True
                scanStatus = False
            return scanStatus   
    def SetForkliftInMiddlePoint(self):
        status = False
        self.ServoAngle = 0.0
        self.DistanceToPublish.Id = self.LastDistanceToPublish.Id + 1
        self.DistanceToPublish.Distance = self.CalculateRoadToMiddlePoint()
        if self.DistanceToPublish.Distance != 0 and self.DistanceToPublish.Id != self.LastDistanceToPublish.Id:
            self.servoAnglePub.publish(self.ServoAngle)
            while self.ServoAngle != self.ServoAngleNow:
                if (self.ServoAngle - 0.1 <= self.ServoAngleNow <= self.ServoAngle + 0.1):
                    self.PrintGreen('servo angle achieved! Will continue in 0.3 seconds...')
                    sleep(0.3)
                    break
                sleep(0.1)
            self.distancePub.publish(self.DistanceToPublish)
            self.PrintGreen(f'Published distance data: {self.DistanceToPublish}')
            self.LastDistanceToPublish = self.DistanceToPublish
            sleep(0.1)
            self.curtisPowerPub.publish(self.CurtisPower)
            self.PrintGreen(f'Published requested curtis power: {self.CurtisPower} PWM')
            distanceLimiter = self.DistanceNow + self.LastDistanceToPublish.Distance + 100
            sleep(0.2)
            self.StartDrive = True
            self.startDrivePub.publish(self.StartDrive)
            while not self.PositionReached:
                if self.DistanceNow >= distanceLimiter:
                    rospy.logerr(f'Distance limit exceeded!!')
                    rospy.logerr(f'Distance now: {self.DistanceNow}') 
                    rospy.logerr(f'Distance limit: {distanceLimiter}')
                    self.cancelDrivePub.publish(True)
                    sleep(0.1)
                    break
                if self.PositionReached:
                    self.PrintGreen('Position reached!')
                    sleep(0.3)
                    break
            if self.PositionReached:
                self.PrintGreen('Everything OK. Check forklift position adn continue') 
                status = True           
        else:
            if self.DistanceToPublish.Distance == 0:
                rospy.logerr('Distance to drive is setted to 0 mm. It will go nowhere!')
            if self.DistanceToPublish.Id == self.LastDistanceToPublish.Id:
                rospy.logerr('Navigation by distance can not accept two distances with the same id')
        return status
    def SetForkliftInFronOfPalette(self):
        status = False
        self.DistanceToPublish.Id = self.LastDistanceToPublish.Id + 1
        self.DistanceToPublish.Distance = self.CalculateRoadToFrontOfPallet()
        self.distancePub.publish(self.DistanceToPublish)
        self.LastDistanceToPublish = self.DistanceToPublish
        self.PrintGreen(f'Published distance data: {self.DistanceToPublish}')
        self.servoAnglePub.publish(self.ServoAngle)
        while self.ServoAngle != self.ServoAngleNow:
            if self.ServoAngle -0.1 <= self.ServoAngleNow <= self.ServoAngle + 0.1:
                self.PrintGreen('Servo angle achieved!')
                sleep(0.3)
                break
        if self.ServoAngle == 90.00 or self.ServoAngle == -90.00:
            self.PrintGreen(f'Servo position OK: {self.ServoAngle}')         
        else:
            rospy.logerr(f'Wrong servo position: {self.ServoAngle}')  
        self.curtisPowerPub.publish(self.CurtisPower)
        self.PrintGreen(f'Published requested curtis power: {self.CurtisPower} PWM')
        sleep(0.3)
        distanceLimiter = self.DistanceNow + self.LastDistanceToPublish.Distance + 100
        self.StartDrive = True
        self.startDrivePub.publish(self.StartDrive)
        while not self.PositionReached:
            if self.DistanceNow >= distanceLimiter:
                rospy.logerr(f'Distance limit exceeded!!')
                rospy.logerr(f'Distance now: {self.DistanceNow}') 
                rospy.logerr(f'Distance limit: {distanceLimiter}')
                self.cancelDrivePub.publish(True)
                sleep(0.1)
                break
            if self.PositionReached:
                self.PrintGreen('Position reached!')
                sleep(0.3)
                status = True
                break
        if self.PositionReached:
            self.PrintGreen('Everything OK. Check forklift position adn continue') 
        return status
    def GoUnderThePalette(self):
        status = False
        self.CalculateRoadUnderPalette()
        self.DistanceToPublish.Id = self.LastDistanceToPublish.Id + 1
        self.DistanceToPublish.Distance = self.CalculatedDistanceUnderThePallet
        self.distancePub.publish(self.DistanceToPublish)
        self.ServoAngle = 0.0
        self.LastDistanceToPublish = self.DistanceToPublish
        self.PrintGreen(f'Published distance data: {self.DistanceToPublish}')
        self.servoAnglePub.publish(self.ServoAngle)
        while self.ServoAngle != self.ServoAngleNow:
            if self.ServoAngle -0.1 <= self.ServoAngleNow <= self.ServoAngle + 0.1:
                self.PrintGreen('Servo angle achieved!')
                sleep(0.3)
                break
        self.curtisPowerPub.publish(self.CurtisPower)
        self.PrintGreen(f'Published requested curtis power: {self.CurtisPower} PWM')
        sleep(0.3)
        distanceLimiter = self.DistanceNow + self.LastDistanceToPublish.Distance + 30
        self.StartDrive = True
        self.startDrivePub.publish(self.StartDrive)
        while not self.PositionReached:
            if self.DistanceNow >= distanceLimiter:
                rospy.logerr(f'Distance limit exceeded!!')
                rospy.logerr(f'Distance now: {self.DistanceNow}') 
                rospy.logerr(f'Distance limit: {distanceLimiter}')
                self.cancelDrivePub.publish(True)
                sleep(0.1)
                break
            if self.PositionReached:
                self.PrintGreen('Position reached!')
                sleep(0.3)
                status = True
                break
        if self.PositionReached:
            self.PrintGreen('Everything OK. Check forklift position adn continue') 
        return status
    def GoOutWithPalette(self):
        status = False
        self.DistanceToPublish.Id = self.LastDistanceToPublish.Id + 1
        self.DistanceToPublish.Distance = self.GoOutFirstDistance 
        self.distancePub.publish(self.DistanceToPublish)
        self.LastDistanceToPublish = self.DistanceToPublish
        self.ServoAngle = self.GoOutFirstServoAngle
        self.PrintGreen(f'Published distance data: {self.DistanceToPublish}')
        self.servoAnglePub.publish(self.ServoAngle)
        while self.ServoAngle != self.ServoAngleNow:
            if self.ServoAngle -0.1 <= self.ServoAngleNow <= self.ServoAngle + 0.1:
                self.PrintGreen('Servo angle achieved!')
                sleep(0.3)
                break
        self.curtisPowerPub.publish(self.CurtisPower)
        self.PrintGreen(f'Published requested curtis power: {self.CurtisPower} PWM')
        sleep(0.3)
        distanceLimiter = self.DistanceNow + self.LastDistanceToPublish.Distance + 30
        self.StartDrive = True
        self.startDrivePub.publish(self.StartDrive)
        while not self.PositionReached:
            if self.DistanceNow >= distanceLimiter:
                rospy.logerr(f'Distance limit exceeded!!')
                rospy.logerr(f'Distance now: {self.DistanceNow}') 
                rospy.logerr(f'Distance limit: {distanceLimiter}')
                self.cancelDrivePub.publish(True)
                sleep(0.1)
                break
            if self.PositionReached:
                self.PrintGreen('Position reached!')
                sleep(0.3)
                status = True
                break
        if self.PositionReached:
            self.PrintGreen('Everything OK. Check forklift position adn continue') 
        self.DistanceToPublish.Id = self.LastDistanceToPublish.Id + 1
        self.DistanceToPublish.Distance = self.GoOutSecondDistance 
        self.distancePub.publish(self.DistanceToPublish)
        self.LastDistanceToPublish = self.DistanceToPublish
        self.ServoAngle = self.GoOutSecondServoAngle
        self.PrintGreen(f'Published distance data: {self.DistanceToPublish}')
        self.servoAnglePub.publish(self.ServoAngle)
        while self.ServoAngle != self.ServoAngleNow:
            if self.ServoAngle -0.1 <= self.ServoAngleNow <= self.ServoAngle + 0.1:
                self.PrintGreen('Servo angle achieved!')
                sleep(0.3)
                break
        self.curtisPowerPub.publish(self.CurtisPower)
        self.PrintGreen(f'Published requested curtis power: {self.CurtisPower} PWM')
        sleep(0.3)
        distanceLimiter = self.DistanceNow + self.LastDistanceToPublish.Distance + 30
        self.StartDrive = True
        self.startDrivePub.publish(self.StartDrive)
        while not self.PositionReached:
            if self.DistanceNow >= distanceLimiter:
                rospy.logerr(f'Distance limit exceeded!!')
                rospy.logerr(f'Distance now: {self.DistanceNow}') 
                rospy.logerr(f'Distance limit: {distanceLimiter}')
                self.cancelDrivePub.publish(True)
                sleep(0.1)
                break
            if self.PositionReached:
                self.PrintGreen('Position reached!')
                sleep(0.3)
                status = True
                break
        if self.PositionReached:
            self.PrintGreen('Everything OK. Check forklift position adn continue') 
        return status
    def WorkSelector(self):
        if not self.InMiddlePoint and not self.InFrontOfPalette and not self.UnderPalette and self.PaletteScanRequest:
            rospy.loginfo("Starting palette scanning....")
            self.PaletteLocalized = self.SearchPalette()
            rospy.loginfo(f'Palette localization confirmation: {self.PaletteLocalized}')
        if not self.InMiddlePoint and not self.InFrontOfPalette and not self.UnderPalette and self.PaletteLocalized and self.GoToMiddlePoint:
            rospy.loginfo("Setting the forklift in the middle point...")
            self.InMiddlePoint = self.SetForkliftInMiddlePoint()
            rospy.loginfo(f'Forklift in palette middle point: {self.InMiddlePoint}')
        if self.InMiddlePoint and self.PaletteLocalized and not self.InFrontOfPalette and not self.UnderPalette and self.GoInFront:
            rospy.loginfo('Setting the forklift in front of a palette...')
            self.InFrontOfPalette = self.SetForkliftInFronOfPalette()
            rospy.loginfo(f'Forklift in front of palette: {self.InFrontOfPalette}')
            self.InMiddlePoint = not self.InFrontOfPalette
        if self.InFrontOfPalette and self.PaletteLocalized and not self.InMiddlePoint and not self.UnderPalette and self.GoUnderPalette:
            rospy.loginfo('Going under palette...')
            self.UnderPalette = self.GoUnderThePalette()
            rospy.loginfo(f'Forklift under the palette: {self.UnderPalette}')
            self.InFrontOfPalette = not self.UnderPalette
        if self.UnderPalette and self.PaletteLocalized and not self.InMiddlePoint and not self.InFrontOfPalette and self.GoOut:
            rospy.loginfo('Going out wiht palette...')
            self.InMiddlePoint = self.GoOutWithPalette()
            rospy.loginfo(f'Forklift getted back to middle point with the palette: {self.InMiddlePoint}')
            self.UnderPalette = not self.InMiddlePoint
        
        
if __name__ == '__main__':
    try:    
        rospy.init_node('MagazineDriverNode')
        magazineDriver = MagazineDriver()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        