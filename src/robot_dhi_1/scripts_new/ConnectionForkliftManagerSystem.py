#!/usr/bin/env python3
import os
import socket
from time import sleep
import rospy
from std_msgs.msg import Int64, Float32, Bool, String
from geometry_msgs.msg import Pose2D
from robot_dhi_1.msg import FlexiReads, WorkstateRead, TaskMessages, FleetManagerCommandsIn as FmsCommandsIn, FleetManagerCommandsOut as FmsCommandsOut
from robot_dhi_1.msg import FleetManagerForkliftDataOut as FmsDataOut, FleetManagerParametersIn as FmsParametersIn, FleetManagerSafetySignalsOut as FmsSSO
from robot_dhi_1.msg import FleetManagerTaskDataIn as FmsTaskIn, FleetManagerTaskDataOut as FmsTaskOut
import struct
import datetime
import asyncio


class FmsCommModule:
    def __init__(self):
        #Parametry polaczenia
        self.FmsAddressIP = '192.168.1.13'
        self.FmsPort = 8000
        self.SystemAdress = (self.FmsAddressIP, self.FmsPort)
        self.FMS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.RefreshRate = rospy.Rate(20)
        self.FMS.settimeout(10.0)
        #Dedklaracje zmiennych globalnych
        self.FirstCycle = True
        self.FmsCommandsIn = FmsCommandsIn()
        self.FmsCommandsOut = FmsCommandsOut()
        self.FmsDataOut = FmsDataOut()
        self.FmsParametersIn = FmsParametersIn()
        self.FmsSafetySignalsOut = FmsSSO()
        self.FmsTaskDataIn = FmsTaskIn()
        self.FmsTaskDataOut = FmsTaskOut()
        self.TaskQueueReceived = ''
        self.TaskQueueToFMS = []
        self.DataToSend = []
        self.DataReceived = []
        self.CommandsReceived = []
        self.BytesToSend = ''
        self.BytesReceived = ''
        rospy.loginfo('connecting to: %s port %s' %self.SystemAdress)
        while not rospy.is_shutdown():
            try:
                #Proba polaczenia z systemem zarzadzajacym
                self.FMS.connect(self.SystemAdress)
                #Deklaracje subscriberow
                self.battery_voltage_sub = rospy.Subscriber('Forklift/state/battery_voltage', Float32, self.CurrentBatteryVoltageCallback)
                self.battery_percentage_sub = rospy.Subscriber('Forklift/state/battery_percentage', Float32, self.CurrentBaterryPercentageCallback)
                self.battery_critical_sub = rospy.Subscriber('Forklift/state/battery_critical_state', Bool, self.CurrentBatteryCriticalStateCallback)
                self.encoder_speed_sub = rospy.Subscriber('PLC/read/encoder_speed', Int64, self.CurrentSpeedCallback)
                self.servo_angle_sub = rospy.Subscriber('Forklift/drive/current_servo_angle', Float32, self.CurrentServoAngleCallback)
                self.forkliftLocalizationSub = rospy.Subscriber('sickLidarPose2D', Pose2D, self.LidarLocPositionCallback)
                self.safetyStatusSub = rospy.Subscriber('Forklift/state/safety/safety_status', FlexiReads, self.SafetySignalsCallback)
                self.activeWorkstatesSub = rospy.Subscriber('Forklift/state/workstates/PLC_active', WorkstateRead, self.CurrentWorkstatesCallback)
                self.cargoWeightSub = rospy.Subscriber('Forklift/forks/cargo_weight', Int64, self.CurrentCargoWeightCallback)
                self.currentForkHeightSub = rospy.Subscriber('Forklift/forks/forks_height', Int64, self.CurrentForksHeightCallback)
                self.currentPwmSub = rospy.Subscriber('Forklift/control/PWM_curtis', Int64, self.CurrentPWMCallback)
                self.confirmCommandsSub = rospy.Subscriber('Forklift/state/WMS/confirmCommand', FmsCommandsOut, self.CommandsConfirmationsCallback)
                self.activeTaskSub = rospy.Subscriber('Forklift/state/WMS/activeTask', FmsTaskOut, self.ActiveTaskCallback)
                self.queuedTaskSub = rospy.Subscriber('Forklift/state/WMS/queuedTasks', String, self.QueuedTaskCallback)
                #Deklaracje publisherow
                self.receivedTaskPub = rospy.Publisher('Forklift/state/WMS/receivedTask', FmsTaskIn, queue_size=1)
                self.receivedCommandsPub = rospy.Publisher('Forklift/state/WMS/receivedCommand', FmsCommandsIn, queue_size=1)
            except(rospy.ServiceException, rospy.ROSException, socket.error) as e:
                self.log_level = 4
                self.log_message = str(e)
            self.CommunicationSequence()
            self.ProgramTestPrint()
            self.RefreshRate.sleep()
    def CurrentBatteryVoltageCallback(self, msg):
        self.FmsDataOut.CurrentBatteryVoltage = round(msg.data, 2)
    def CurrentBaterryPercentageCallback(self, msg):
        if msg.data >= 95.0:
            self.FmsDataOut.CurrentBatteryPercentage = 100.0
        elif msg.data >= 85.0:
            self.FmsDataOut.CurrentBatteryPercentage = 90.0
        elif msg.data >= 75.0:
            self.FmsDataOut.CurrentBatteryPercentage = 80.0
        elif msg.data >= 65.0:
            self.FmsDataOut.CurrentBatteryPercentage = 70.0
        elif msg.data >= 55.0:
            self.FmsDataOut.CurrentBatteryPercentage = 60.0
        elif msg.data >= 45.0:
            self.FmsDataOut.CurrentBatteryPercentage = 50.0
        elif msg.data >= 35.0:
            self.FmsDataOut.CurrentBatteryPercentage = 40.0
        elif msg.data >= 25.0:
            self.FmsDataOut.CurrentBatteryPercentage = 30.0
        elif msg.data >= 15.0:
            self.FmsDataOut.CurrentBatteryPercentage = 20.0
        elif msg.data >= 5.0:
            self.FmsDataOut.CurrentBatteryPercentage = 10.0
        else:
            self.FmsDataOut.CurrentBatteryPercentage = 0.0
    def CurrentBatteryCriticalStateCallback(self, msg):
        self.FmsDataOut.BatteryStateCritical = msg.data
    def CurrentSpeedCallback(self, msg):
        self.FmsDataOut.CurrentVehicleSpeed = round((msg.data / 100), 2)
    def CurrentServoAngleCallback(self, msg):
        self.FmsDataOut.CurrentSteeringAngle = round(msg.data, 2)
    def LidarLocPositionCallback(self, msg):
        self.FmsDataOut.CurrentPositionX = msg.x
        self.FmsDataOut.CurrentPositionY = msg.y
        self.FmsDataOut.CurrentPositionTheta = round(msg.theta, 3)
    def SafetySignalsCallback(self, msg):
        self.FmsSafetySignalsOut.LeftScannerEmergencyZoneStatus = msg.LeftScannerEmergencyZoneStatus
        self.FmsSafetySignalsOut.LeftScannerSoftStopZoneStatus = msg.LeftScannerSoftStopZoneStatus
        self.FmsSafetySignalsOut.LeftScannerReducedSpeedZoneStatus = msg.LeftScannerReducedSpeedZoneStatus
        self.FmsSafetySignalsOut.RightScannerEmergencyZoneStatus = msg.RightScannerEmergencyZoneStatus
        self.FmsSafetySignalsOut.RightScannerSoftStopZoneStatus = msg.RightScannerSoftStopZoneStatus
        self.FmsSafetySignalsOut.RightScannerReducedSpeedZoneStatus = msg.RightScannerReducedSpeedZoneStatus
        self.FmsSafetySignalsOut.LeftScannerContaminationWarning = bool(-msg.LeftScannerContaminationWarning)
        self.FmsSafetySignalsOut.LeftScannerContaminationError = bool(msg.LeftScannerContaminationError)
        self.FmsSafetySignalsOut.LeftScannerAppError = bool(msg.LeftScannerAppError)
        self.FmsSafetySignalsOut.LeftScannerDeviceError = bool(msg.LeftScannerDeviceError)
        self.FmsSafetySignalsOut.LeftScannerActive = msg.LeftLidarActive
        self.FmsSafetySignalsOut.RightScannerContaminationWarning = bool(-msg.RightScannerContaminationWarning)
        self.FmsSafetySignalsOut.RightScannerContaminationError = bool(msg.RightScannerContaminationError)
        self.FmsSafetySignalsOut.RightScannerAppError = bool(msg.RightScannerAppError)
        self.FmsSafetySignalsOut.RightScannerDeviceError = bool(msg.RightScannerDeviceError)
        self.FmsSafetySignalsOut.RightScannerActive = msg.RightLidarActive
        self.FmsSafetySignalsOut.StandstillStatus = msg.Standstill
    def CurrentWorkstatesCallback(self, msg):
        self.FmsDataOut.S0_1 = msg.S0_1
        self.FmsDataOut.S0_2 = msg.S0_2
        self.FmsDataOut.S0_3 = msg.S0_3
        self.FmsDataOut.S1 = msg.S1
        self.FmsDataOut.S2 = msg.S2
        self.FmsDataOut.S3 = msg.S3
        self.FmsDataOut.S4 = msg.S4
        self.FmsDataOut.S4_0 = msg.S4_0
        self.FmsDataOut.S4_1 = msg.S4_1
        self.FmsDataOut.S4_2 = msg.S4_2
        self.FmsDataOut.S4_3 = msg.S4_3
        self.FmsDataOut.S4_4 = msg.S4_4
        self.FmsDataOut.S4_5 = msg.S4_5
        self.FmsDataOut.S4_6 = msg.S4_6
    def CurrentCargoWeightCallback(self, msg):
        self.FmsDataOut.CurrentCargoWeight = msg.data
    def CurrentForksHeightCallback(self, msg):
        self.FmsDataOut.CurrentForksHeight = msg.data
    def CurrentPWMCallback(self, msg):
        self.FmsDataOut.CurrentPWM = msg.data
    def CommandsConfirmationsCallback(self, msg):
        self.FmsCommandsOut = msg
    def ActiveTaskCallback(self, msg):
        self.FmsTaskDataOut = msg
    def QueuedTaskCallback(self, msg):
        self.TaskQueueReceived = msg.data
        splittedData = self.TaskQueueReceived.split('#')
        if len(splittedData[0]) > 0:
            for item in splittedData:
                self.TaskQueueToFMS.append(item)
    def CreateDataToSend(self):
        rospy.loginfo('Creating datatable to send')
        self.FmsDataOut.DataRefreshTime = datetime.datetime.now()
        self.DataToSend.append(self.FmsDataOut.DataRefreshTime)
        self.DataToSend.append(self.FmsDataOut.CurrentBatteryVoltage)
        self.DataToSend.append(self.FmsDataOut.CurrentBatteryPercentage)
        self.DataToSend.append(self.FmsDataOut.BatteryStateCritical)
        self.DataToSend.append(self.FmsDataOut.CurrentPositionX)
        self.DataToSend.append(self.FmsDataOut.CurrentPositionY)
        self.DataToSend.append(self.FmsDataOut.CurrentPositionTheta)
        self.DataToSend.append(self.FmsDataOut.CurrentPWM)
        self.DataToSend.append(self.FmsDataOut.CurrentVehicleSpeed)
        self.DataToSend.append(self.FmsDataOut.CurrentSteeringAngle)
        self.DataToSend.append(self.FmsDataOut.CurrentTiltAngleAxis1)
        self.DataToSend.append(self.FmsDataOut.CurrentTiltAngleAxis2)
        self.DataToSend.append(self.FmsDataOut.CurrentCargoWeight)
        self.DataToSend.append(self.FmsDataOut.CurrentForksHeight)
        self.DataToSend.append(self.FmsDataOut.S0_1)
        self.DataToSend.append(self.FmsDataOut.S0_2)
        self.DataToSend.append(self.FmsDataOut.S0_3)
        self.DataToSend.append(self.FmsDataOut.S1)
        self.DataToSend.append(self.FmsDataOut.S2)
        self.DataToSend.append(self.FmsDataOut.S3)
        self.DataToSend.append(self.FmsDataOut.S4)
        self.DataToSend.append(self.FmsDataOut.S4_0)
        self.DataToSend.append(self.FmsDataOut.S4_1)
        self.DataToSend.append(self.FmsDataOut.S4_2)
        self.DataToSend.append(self.FmsDataOut.S4_3)
        self.DataToSend.append(self.FmsDataOut.S4_4)
        self.DataToSend.append(self.FmsDataOut.S4_5)
        self.DataToSend.append(self.FmsDataOut.S4_6)
        self.DataToSend.append('&')
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerEmergencyZoneStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerSoftStopZoneStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerReducedSpeedZoneStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerContaminationWarning)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerContaminationError)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerAppError)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerDeviceError)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftScannerActive)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerEmergencyZoneStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerSoftStopZoneStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerReducedSpeedZoneStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerContaminationWarning)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerContaminationError)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerAppError)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerDeviceError)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightScannerActive)
        self.DataToSend.append(self.FmsSafetySignalsOut.LeftEmergencyStopButtonStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.RightEmergencyStopButtonStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.SafetyEncoderStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.FlexiCPUStatus)
        self.DataToSend.append(self.FmsSafetySignalsOut.StandstillStatus)
        self.DataToSend.append('&')
        self.DataToSend.append(self.FmsCommandsOut.ConfirmStartAutoMode)
        self.DataToSend.append(self.FmsCommandsOut.ConfirmPauseWork)
        self.DataToSend.append(self.FmsCommandsOut.ConfirmContinueWork)
        self.DataToSend.append(self.FmsCommandsOut.ConfirmEmergencyStop)
        self.DataToSend.append(self.FmsCommandsOut.ConfirmCancelLastTask)
        self.DataToSend.append(self.FmsCommandsOut.ConfirmDeleteAllTask)
        self.DataToSend.append('&')
        if self.FmsTaskDataOut.CurrentTaskID == '':
            self.FmsTaskDataOut.CurrentTaskID = "No ID"
        if self.FmsTaskDataOut.CurrentTaskReceivedDate == '':
            self.FmsTaskDataOut.CurrentTaskReceivedDate = "No Date"
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskID)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskReceivedDate)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskType)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskImportanceLevel)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskCoordinatesX)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskCoordinatesY)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskCoordinatesTetha)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskIsInQueue)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskIsInProgress)
        self.DataToSend.append(self.FmsTaskDataOut.CurrentTaskIsDone)
        self.DataToSend.append('&')
        if self.TaskQueueToFMS is not None:
            for item in self.TaskQueueToFMS:
                self.DataToSend.append(item)
        else:
            self.DataToSend.append('No task queue data received')
        self.DataToSend.append('&')
        print(self.FmsTaskDataOut)
    def CreateBytesToSend(self):
        rospy.loginfo('Converting data and creating bytes to send')
        self.DataToSend = [str(item) if item is not None else 0 for item in self.DataToSend]
        for item in self.DataToSend:
            self.BytesToSend = self.BytesToSend + item + '#'
    def publishReceivedData(self):
        if len(self.DataReceived) >= 7:
            if self.DataReceived[0] != '':
                self.FmsTaskDataIn.TaskID = self.DataReceived[0]
                self.FmsTaskDataIn.TaskDate = self.DataReceived[1]
                self.FmsTaskDataIn.TaskType = int(self.DataReceived[2])
                self.FmsTaskDataIn.ImportanceLevel = int(self.DataReceived[3])
                self.FmsTaskDataIn.CoordinatesX = float(self.DataReceived[4])
                self.FmsTaskDataIn.CoordinatesY = float(self.DataReceived[5])
                self.FmsTaskDataIn.CoordinatesTetha = float(self.DataReceived[6])   
                self.receivedTaskPub.publish(self.FmsTaskDataIn)
                rospy.loginfo(self.FmsTaskDataIn)
    def publishReceivedCommands(self):
        if len(self.CommandsReceived) >= 7:
            self.FmsCommandsIn.StartAutoMode = bool(self.CommandsReceived[0]) == "True"
            self.FmsCommandsIn.ContinueWork = bool(self.CommandsReceived[1]) == "True"
            self.FmsCommandsIn.PauseWork = bool(self.CommandsReceived[2]) == "True"
            self.FmsCommandsIn.EmergencyStop = bool(self.CommandsReceived[3]) == "True"
            self.FmsCommandsIn.CancelLastTask = bool(self.CommandsReceived[4]) == "True"
            self.FmsCommandsIn.DeleteAllTask = bool(self.CommandsReceived[5]) == "True"
            self.FmsCommandsIn.ManualModeOverride = bool(self.CommandsReceived[6]) == "True"
            self.receivedCommandsPub.publish(self.FmsCommandsIn)
        # rospy.loginfo(self.FmsCommandsIn)
        # rospy.loginfo(self.CommandsReceived)
        # self.receivedCommandsPub.publish(self.FmsCommandsIn)
    def SendBytes(self):
        try:
            rospy.loginfo('Sending bytes to system')
            message = bytes(self.BytesToSend + '$', 'ascii')
            rospy.loginfo(message)
            self.FMS.send(message)
        except BrokenPipeError:
            rospy.loginfo('Broken pipe error, reconnecting')
            self.Reconnect()
    def ClearData(self):
        rospy.loginfo('Clearing data table and bytes')
        self.DataToSend.clear()
        self.BytesToSend = ''
    def Reconnect(self):
        self.FMS.close()
        self.FMS = None
        while self.FMS is None:
            try:
                self.FMS = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.FMS.connect(self.SystemAdress)
                break;
            except (rospy.ServiceException, rospy.ROSException, socket.error) as e:
                rospy.loginfo('Reconnection failed: %s. Retryin in 10 seconds...' % e)
                sleep(1)
    def ProgramTestPrint(self):
        rospy.loginfo(len(self.DataToSend))
    def ReadBytes(self):
        try:
            self.BytesReceived = self.FMS.recv(65535)
            if len(self.BytesReceived) > 0:
                stringReceived = self.BytesReceived.decode("ascii")
                rospy.loginfo(stringReceived)
                listDatasets = []
                listDatasets = stringReceived.split('&')
                self.DataReceived = listDatasets[0].split('#')
                self.DataReceived = [str(item) if item is not None else 0 for item in self.DataReceived]
                self.CommandsReceived = listDatasets[1].split('#')
                # self.CommandsReceived = [str(item) if item is not '' else 0 for item in self.CommandsReceived]
        except (BrokenPipeError, socket.error):
            rospy.loginfo('Broken pipe error, reconnecting...')
            self.Reconnect()
    def CommunicationSequence(self):
        self.CreateDataToSend()
        self.CreateBytesToSend()
        if len(self.BytesToSend) > 0:
            self.SendBytes()
        self.ReadBytes()
        self.publishReceivedData()
        self.publishReceivedCommands()
        self.ClearData()
        
if __name__ == '__main__':
    try:    
        rospy.init_node('ForkliftManagerSystemCOnnectionNode')
        ForkliftManagementSystemCommunication = FmsCommModule()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')