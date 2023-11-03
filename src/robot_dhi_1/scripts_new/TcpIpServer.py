#!/usr/bin/env python3
import os
import socket
from time import sleep
import rospy
from std_msgs.msg import Int64, Float32, Bool, String
from geometry_msgs.msg import Pose2D
from robot_dhi_1.msg import FlexiReads, WorkstateRead, FleetManagerTaskDataIn as FMSTaskIn, LogMessages
from robot_dhi_1.msg import TEBConfigMessages as TEB, FleetManagerTaskDataOut as TaskOut
from robot_dhi_1.msg import FleetManagerCommandsIn as CommandsIn, FleetManagerCommandsOut as CommandsOut
import struct
import datetime
import netifaces

class TCPServer:
    def __init__(self, host, port):
        self.ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ServerSocket.bind((host, port))
        self.ServerSocket.listen(5)
        rospy.loginfo(f"Server listening on {host}:{port}....")
    def AcceptConnection(self):
        clientSocket, addr = self.ServerSocket.accept()
        rospy.loginfo(f"Accepted connection from {addr[0]}:{addr[1]}")
        return clientSocket
    def close(self):
        self.ServerSocket.close()
class CommunicationModule:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        rospy.loginfo("initializing communication module..")
        self.ServerAddress = ''
        self.battery_voltage = ''
        self.battery_percentage = ''
        self.battery_critical = ''
        self.bytes_to_send = ''
        self.bytes_received = ''
        self.forklift_parameters = ''
        self.battery_parameters = ''
        self.motion_parameters = ''
        self.safetyParameters = ''
        self.currentPwm = ''
        self.workstateParameters = ''
        self.speed_actual = ''
        self.servo_angle = ''
        self.cargoWeight = ''
        self.forksHeight = ''
        self.OldJobID = 'a'
        self.sendData = []
        self.receivedTebParameters = []
        self.receivedCommands = []
        self.receivedTaskData = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rate = rospy.Rate(10)
        self.currentLocMessage = ''
        self.activeWorkstate = WorkstateRead()
        self.safetyStatus = FlexiReads()
        self.lidarlocPose = Pose2D()
        self.taskReceived = FMSTaskIn()
        self.ServerStartup = True
        self.ForkliftLog = LogMessages()
        self.ForkliftLogOld = LogMessages()
        self.ForkliftLogSend = False
        self.ForkliftLogReaded = False
        self.TiltAxis1 = 0
        self.TiltAxis2 = 0
        self.batteryPercentageOld = 100.0
        self.batteryVoltageOld = 100.0
        gateways = netifaces.gateways()
        defaultGateway = gateways['default'][netifaces.AF_INET][1]
        self.ServerAddress = netifaces.ifaddresses(defaultGateway)[netifaces.AF_INET][0]['addr']
        self.receivedTebParams = TEB()
        self.readedTebParams = TEB()
        self.savedTebParamsConfirmation = False
        self.NfcCardId = ''
        self.TaskConfirmations = TaskOut()
        self.CommandsReceived = CommandsIn()
        self.CommandsConfirmations = CommandsOut()
        rospy.loginfo(self.ServerAddress)
        self.startup = True
        self.Server = TCPServer(self.ServerAddress, 2137)
        while not rospy.is_shutdown():
            try:
                
                if self.ServerStartup:
                    rospy.loginfo('Trying to accept connection')
                    self.sock = self.Server.AcceptConnection()
                    self.ServerStartup = False
                self.battery_voltage_sub = rospy.Subscriber('Forklift/state/battery_voltage', Float32, self.battery_voltage_read)
                self.battery_percentage_sub = rospy.Subscriber('Forklift/state/battery_percentage', Float32, self.battery_percentage_read)
                self.battery_critical_sub = rospy.Subscriber('Forklift/state/battery_critical_state', Bool, self.battery_critical_read)
                self.encoder_speed_sub = rospy.Subscriber('PLC/read/encoder_speed', Int64, self.encoder_speed_read)
                self.servo_angle_sub = rospy.Subscriber('Forklift/drive/current_servo_angle', Float32, self.servo_angle_read)
                self.forkliftLocalizationSub = rospy.Subscriber('sickLidarPose2D', Pose2D, self.currentLocRead)
                self.safetyStatusSub = rospy.Subscriber('Forklift/state/safety/safety_status', FlexiReads, self.safetyRead)
                self.activeWorkstatesSub = rospy.Subscriber('Forklift/state/workstates/Active', WorkstateRead, self.activeWorkstateRead)
                self.cargoWeightSub = rospy.Subscriber('Forklift/forks/cargo_weight', Int64, self.cargoWeightRead)
                self.currentForkHeightSub = rospy.Subscriber('Forklift/forks/forks_height', Int64, self.forkHeightRead)
                self.currentPwmSub = rospy.Subscriber('Forklift/control/PWM_curtis', Int64, self.currentPWMRead)
                self.TaskConfirmationsSub = rospy.Subscriber('Forklift/state/FMS/confirmations', TaskOut, self.TaskOutCallback)
                self.confirmCommandsSub = rospy.Subscriber('Forklift/state/FMS/confirmCommand', CommandsOut, self.confirmationCommandsCallback)
                self.tiltAxis1Sub = rospy.Subscriber('Forklift/sensors/tilt_axis_1', Int64, self.TiltAxis1Callback)
                self.tiltAxis2Sub = rospy.Subscriber('Forklift/sensors/tilt_axis_1', Int64, self.TiltAxis2Callback)
                self.NfcSub = rospy.Subscriber('Forklift/state/user/card_id', String,self.NfcCardCallback)
                self.LogsSub = rospy.Subscriber('Forklift/state/log', LogMessages, self.LogCallback)
                self.ReadedTebParamsSub = rospy.Subscriber('Forklift/cfg/current/teb', TEB, self.ReadedTebParamsCallback)
                self.TebParamsSaveConfirmationSub = rospy.Subscriber('Forklift/cfg/current/teb/confirmation', Bool, self.TebParamsSaveConfirmationCallback)
                self.ReceivedTebParamspub = rospy.Publisher('Forklift/cfg/received/teb', TEB, queue_size=1, latch=True)
                self.receivedTaskPub = rospy.Publisher('Forklift/state/FMS/Task/received', FMSTaskIn, queue_size=1)
                self.receivedCommandsPub = rospy.Publisher('Forklift/state/FMS/receivedCommand', CommandsIn, queue_size=1)
            except(rospy.ServiceException, rospy.ROSException, socket.error) as e:
                self.log_level = 4
                self.log_message = str(e)
                rospy.loginfo(e)
            self.communication()
            rospy.loginfo('Refresh rate started')
            self.rate.sleep()
    def TaskOutCallback(self, msg):
        self.TaskConfirmations = msg
    def LogCallback(self, msg):
        self.ForkliftLog = msg
        if self.ForkliftLog.Date != self.ForkliftLogOld.Date:
            self.ForkliftLogOld = self.ForkliftLog          
    def Reconnect(self):
        rospy.loginfo('Client disconnected! Starting reconnecting module....')
        self.sock.close()
        self.sock = self.Server.AcceptConnection()
        rospy.loginfo("Client reconnected")
    def ReadedTebParamsCallback(self, msg):
        self.readedTebParams = msg
    def TebParamsSaveConfirmationCallback(self, msg):
        self.savedTebParamsConfirmation = msg.data
    def NfcCardCallback(self,msg):
        data = msg.data
        if data == '':
            self.NfcCardId ='No card'
        else:
            self.NfcCardId = data
    def TiltAxis1Callback(self, msg):
        data = msg.data
        self.TitlAxis1 = data
    def TiltAxis2Callback(self, msg):
        data = msg.data
        self.TiltAxis2 = data
    def activeTaskCallback(self, msg):
        self.activeTask = msg
    def queuedTasksCallback(self, msg):
        self.queuedTasks = msg.data
    def confirmationCommandsCallback(self, msg):
        self.FMCconfirmations = msg
    def currentPWMRead(self, msg):
        data = msg.data
        self.currentPwm = str(data)
    def cargoWeightRead(self, msg):
        data = msg.data
        self.cargoWeight = str(data)
    def forkHeightRead(self, msg):
        data = msg.data
        self.forksHeight = str(data)
    def safetyRead(self, msg):
        self.safetyStatus = msg
    def activeWorkstateRead(self, msg):
        self.activeWorkstate = msg
    def currentLocRead(self, msg):
        self.lidarlocPose = msg
    def servo_angle_read(self, msg):
        dataTmp = msg.data
        data = 0.0
        if dataTmp == -0.0:
            data == 0.0
        else:
            data = dataTmp
        self.servo_angle = str(round(data, 2))
    def battery_voltage_read(self, msg):
        data = msg.data
        if data < self.batteryVoltageOld:
            self.battery_voltage = str(round(data, 2))
            self.batteryVoltageOld = data       
    def battery_percentage_read(self, msg):
        data = msg.data
        if data < self.batteryPercentageOld:
            self.battery_percentage = str(round(data, 2))
            self.batteryPercentageOld = data
    def battery_critical_read(self, msg):
        data = msg.data
        if data:
            self.battery_critical = 'true'
        else:
            self.battery_critical = 'true'
    def encoder_speed_read(self, msg):
        data = msg.data
        self.speed_actual = str(round((data / 100), 2))
    def createDataList(self):
        self.sendData.append(self.battery_voltage)
        self.sendData.append(self.battery_percentage)
        self.sendData.append(self.battery_critical)
        self.sendData.append(self.lidarlocPose.x)
        self.sendData.append(self.lidarlocPose.y)
        self.sendData.append(round(self.lidarlocPose.theta, 3))
        self.sendData.append(self.currentPwm)
        self.sendData.append(self.speed_actual)
        self.sendData.append(self.servo_angle)
        self.sendData.append(self.TiltAxis1)
        self.sendData.append(self.TiltAxis2)
        self.sendData.append(self.cargoWeight)
        self.sendData.append(self.forksHeight)
        self.sendData.append(self.activeWorkstate.S0_1)
        self.sendData.append(self.activeWorkstate.S0_2)
        self.sendData.append(self.activeWorkstate.S0_3)
        self.sendData.append(self.activeWorkstate.S1)
        self.sendData.append(self.activeWorkstate.S2)
        self.sendData.append(self.activeWorkstate.S3)
        self.sendData.append(self.activeWorkstate.S4)
        self.sendData.append(self.activeWorkstate.S4_0)
        self.sendData.append(self.activeWorkstate.S4_1)
        self.sendData.append(self.activeWorkstate.S4_2)
        self.sendData.append(self.activeWorkstate.S4_3)
        self.sendData.append(self.activeWorkstate.S4_4)
        self.sendData.append(self.activeWorkstate.S4_5)
        self.sendData.append(self.activeWorkstate.S4_6)
        self.sendData.append('&')
        self.sendData.append(self.safetyStatus.LeftScannerEmergencyZoneStatus)
        self.sendData.append(self.safetyStatus.LeftScannerSoftStopZoneStatus)
        self.sendData.append(self.safetyStatus.LeftScannerReducedSpeedZoneStatus)
        self.sendData.append(self.safetyStatus.LeftScannerContaminationWarning)
        self.sendData.append(self.safetyStatus.LeftScannerContaminationError)
        self.sendData.append(self.safetyStatus.LeftScannerAppError)
        self.sendData.append(self.safetyStatus.LeftScannerDeviceError)
        self.sendData.append(self.safetyStatus.LeftLidarActive)
        self.sendData.append(self.safetyStatus.RightScannerEmergencyZoneStatus)
        self.sendData.append(self.safetyStatus.RightScannerSoftStopZoneStatus)
        self.sendData.append(self.safetyStatus.RightScannerReducedSpeedZoneStatus)
        self.sendData.append(self.safetyStatus.RightScannerContaminationWarning)
        self.sendData.append(self.safetyStatus.RightScannerContaminationError)
        self.sendData.append(self.safetyStatus.RightScannerAppError)
        self.sendData.append(self.safetyStatus.RightScannerDeviceError)
        self.sendData.append(self.safetyStatus.RightLidarActive)
        self.sendData.append(self.safetyStatus.LeftEmergencyStopStatus)
        self.sendData.append(self.safetyStatus.RightEmergencyStopStatus)
        self.sendData.append(self.safetyStatus.EncoderOK)
        self.sendData.append(self.safetyStatus.CpuOK)
        self.sendData.append(self.safetyStatus.Standstill)
        self.sendData.append('&')
        self.sendData.append(self.NfcCardId)
        self.sendData.append('&')
        self.sendData.append(self.savedTebParamsConfirmation)
        self.sendData.append(self.readedTebParams.ForwardMaxVelX)
        self.sendData.append(self.readedTebParams.BackwardMaxVelX)
        self.sendData.append(self.readedTebParams.MaxVelTheta)
        self.sendData.append(self.readedTebParams.AccLimitX)
        self.sendData.append(self.readedTebParams.AccLimitTheta)
        self.sendData.append(self.readedTebParams.TurningRadius)
        self.sendData.append(self.readedTebParams.Wheelbase)
        self.sendData.append(self.readedTebParams.GoalToleranceXY)
        self.sendData.append(self.readedTebParams.GoalToleranceYaw)
        self.sendData.append(self.readedTebParams.MinObstacleDistance)
        self.sendData.append(self.readedTebParams.ObstacleInflationRadius)
        self.sendData.append(self.readedTebParams.DynamicObstacleInflationRadius)
        self.sendData.append(self.readedTebParams.DTRef)
        self.sendData.append(self.readedTebParams.DTHysteresis)
        self.sendData.append(self.readedTebParams.IncludeDynamicObstacles)
        self.sendData.append(self.readedTebParams.IncludeCostmapObstacles)
        self.sendData.append(self.readedTebParams.OscillationRecovery)
        self.sendData.append(self.readedTebParams.AllowInitializeWithBackwardMotion)
        self.sendData.append('&')
        self.sendData.append(self.TaskConfirmations.TaskID)
        self.sendData.append(self.TaskConfirmations.TaskListID)
        self.sendData.append(self.TaskConfirmations.TaskType)
        self.sendData.append(self.TaskConfirmations.LocationType)
        self.sendData.append(self.TaskConfirmations.CoordinatesX)
        self.sendData.append(self.TaskConfirmations.CoordinatesY)
        self.sendData.append(self.TaskConfirmations.CoordinatesTetha)
        self.sendData.append(self.TaskConfirmations.IsRunning)
        self.sendData.append(self.TaskConfirmations.IsDone)
        self.sendData.append(self.TaskConfirmations.IsCanceled)
        self.sendData.append('&')
        self.sendData.append(self.CommandsConfirmations.ConfirmNewTaskReceived)
        self.sendData.append(self.CommandsConfirmations.ConfirmContinueWork)
        self.sendData.append(self.CommandsConfirmations.ConfirmPauseWork)
        self.sendData.append(self.CommandsConfirmations.ConfirmEmergencyStop)
        self.sendData.append(self.CommandsConfirmations.ConfirmCancelLastTask)
        self.sendData.append(self.CommandsConfirmations.ConfirmStartTask)
        # Przekształć każdy element w liście na string i zastąp oryginalną listę nową listą zawierającą stringi
        self.sendData = [str(item) if item is not None else '0' for item in self.sendData]
        self.sendData.append('!')
    def clearData(self):
        self.sendData.clear()
        self.bytes_to_send = ''
        self.receivedTebParameters.clear()
    def convertSendData(self):
        for item in self.sendData:
            self.bytes_to_send = self.bytes_to_send + item + '#'     
    def create_bytes_to_send(self):
        self.createDataList()
        self.convertSendData()
        if self.bytes_to_send != None:
            return True
        else:
            return False    
    def send_bytes(self):
        try:
            message = bytes(self.bytes_to_send + '$', 'ascii')
            self.sock.send(message)
            self.receive_bytes()
        except (BrokenPipeError, ConnectionAbortedError, ConnectionRefusedError, ConnectionResetError,ConnectionError):
            rospy.logerr('Broken pipe error, reconnecting...')
            self.Reconnect()
    def PublishReceivedTebParams(self):
        if len(self.receivedTebParameters) > 1:
            try:
                if (self.receivedTebParameters[0] == 'True'):
                    self.receivedTebParams.SaveSettings = True
                else:
                    self.receivedTebParams.SaveSettings = False
                for r in range(1, 15):
                    if (self.receivedTebParameters[r] == ''):
                        self.receivedTebParameters[r] = 0
                self.receivedTebParams.ForwardMaxVelX = float(self.receivedTebParameters[1])
                self.receivedTebParams.BackwardMaxVelX = float(self.receivedTebParameters[2])
                self.receivedTebParams.MaxVelTheta = float(self.receivedTebParameters[3])
                self.receivedTebParams.AccLimitX = float(self.receivedTebParameters[4])
                self.receivedTebParams.AccLimitTheta = float(self.receivedTebParameters[5])
                self.receivedTebParams.TurningRadius = float(self.receivedTebParameters[6])
                self.receivedTebParams.Wheelbase = float(self.receivedTebParameters[7])
                self.receivedTebParams.GoalToleranceXY = float(self.receivedTebParameters[8])
                self.receivedTebParams.GoalToleranceYaw= float(self.receivedTebParameters[9])
                self.receivedTebParams.MinObstacleDistance = float(self.receivedTebParameters[10])
                self.receivedTebParams.ObstacleInflationRadius = float(self.receivedTebParameters[11])
                self.receivedTebParams.DynamicObstacleInflationRadius = float(self.receivedTebParameters[12])
                self.receivedTebParams.DTRef = float(self.receivedTebParameters[13])
                self.receivedTebParams.DTHysteresis = float(self.receivedTebParameters[14])
                if (self.receivedTebParameters[15] == 'True'):
                    self.receivedTebParams.IncludeDynamicObstacles = True
                else:
                    self.receivedTebParams.IncludeDynamicObstacles = False
                if (self.receivedTebParameters[16] == 'True'):
                    self.receivedTebParams.IncludeCostmapObstacles = True
                else:
                    self.receivedTebParams.IncludeCostmapObstacles = False
                if (self.receivedTebParameters[17] == 'True'):
                    self.receivedTebParams.OscillationRecovery = True
                else:
                    self.receivedTebParams.OscillationRecovery = False
                if (self.receivedTebParameters[18] == 'True'):
                    self.receivedTebParams.AllowInitializeWithBackwardMotion = True
                else:
                    self.receivedTebParams.AllowInitializeWithBackwardMotion = False   
                self.ReceivedTebParamspub.publish(self.receivedTebParams)
                rospy.loginfo("Received TEB Data OK")
            except Exception as e:    
                rospy.loginfo('Problem in received TEB data...')
                rospy.loginfo(e) 
            print('============TEB PARAMETERS RECEIVED================')
            print(self.receivedTebParams)    
    def PublishReceivedTaskData(self):
        if len(self.receivedTaskData) > 1:
            try:
                self.taskReceived.TaskID = int(self.receivedTaskData[0])
                self.taskReceived.TaskListID = int(self.receivedTaskData[1])
                self.taskReceived.TaskType = int(self.receivedTaskData[2])
                self.taskReceived.LocationType = int(self.receivedTaskData[3])
                self.taskReceived.CoordinatesX = float(self.receivedTaskData[4])
                self.taskReceived.CoordinatesY = float(self.receivedTaskData[5])
                self.taskReceived.CoordinatesTetha = float(self.receivedTaskData[6])
                if self.receivedTaskData[7] == 'True':
                    self.taskReceived.RunTask = True
                else:
                    self.taskReceived.RunTask = False
                if self.receivedTaskData[8] == 'True':
                    self.taskReceived.CancelTask = True
                else:
                    self.taskReceived.CancelTask = False
                print('============TASK RECEIVED DATA================')
                print(self.taskReceived)
                self.receivedTaskPub.publish(self.taskReceived)
            except Exception as e:
                rospy.loginfo('Problem in received Task data....')
                rospy.loginfo(e)
    def PublishReceivedCommands(self):
        if len(self.receivedCommands) > 1:
            try:
                if self.receivedCommands[0] == 'True':
                    self.CommandsReceived.InitializeAutoMode = True
                else:
                    self.CommandsReceived.InitializeAutoMode = False
                if self.receivedCommands[1] == 'True':
                    self.CommandsReceived.ManualModeOverride = True
                else:
                    self.CommandsReceived.ManualModeOverride = False
                if self.receivedCommands[2] == 'True':
                    self.CommandsReceived.Pause = True
                else:
                    self.CommandsReceived.Pause = False
                if self.receivedCommands[3] == 'True':
                    self.CommandsReceived.Continue = True
                else:
                    self.CommandsReceived.Continue = False
                if self.receivedCommands[4] == 'True':
                    self.CommandsReceived.EmergencyStop = True
                else:
                    self.CommandsReceived.EmergencyStop = False
                if self.receivedCommands[5] == 'True':
                    self.CommandsReceived.StartTask = True
                else:
                    self.CommandsReceived.StartTask = False
                self.receivedCommandsPub.publish(self.CommandsReceived)
            except Exception as e:
                rospy.loginfo('Problem in received Commands data....')
                rospy.loginfo(e)        
    def noneTypeToFalse(self):
        if self.FMCconfirmations.confirmEmergencyStopForklift is None:
            self.FMCconfirmations.confirmEmergencyStopForklift = False
        if self.FMCconfirmations.confirmStopForklift is None:
            self.FMCconfirmations.confirmStopForklift = False
        if self.FMCconfirmations.continuework is None:
            self.FMCconfirmations.continuework = False
        if self.FMCconfirmations.confirmReset is None:
            self.FMCconfirmations.confirmReset = False
        if self.FMCconfirmations.confirmManualModeOverride is None:
            self.FMCconfirmations.confirmManualModeOverride = False
    def receive_bytes(self):
        try:
            self.bytes_received = self.sock.recv(65535)
            data_string = self.bytes_received.decode("utf-8")  # konwertowanie na string UTF-8
            split_data = data_string.split('&')  # dzielenie na listę
            if len(split_data[0]) > 0:
                self.receivedTebParameters = split_data[0].split('#')
                self.PublishReceivedTebParams()
            elif len(split_data[0]) <=0:
                rospy.loginfo('split_data[0] <= 0 !!!!!')
            if len(split_data) >= 2:
                if len(split_data[1]) > 0:
                    self.receivedTaskData = split_data[1].split('#')    
                    self.PublishReceivedTaskData()
                elif len(split_data[1]) <=0:
                    rospy.loginfo('No task data')
            if len(split_data) >= 3:
                if len(split_data[2]) > 0:
                    self.receivedCommands = split_data[2].split('#')
                    self.PublishReceivedCommands()
                elif len(split_data[2]) <= 0:
                    rospy.loginfo('No commands data')
                
        except (BrokenPipeError, socket.error):
            rospy.logerr('Broken pipe error in receiving, reconnecting...')
            self.Reconnect()
    def communication(self):
        os.system('clear')
        # rospy.loginfo(self.sock)
        create_check = self.create_bytes_to_send()
        if create_check:
            self.send_bytes()
        # self.receive_bytes()
        self.rate.sleep()
        self.clearData()
        self.startup = False
if __name__ == '__main__':
    try:    
        rospy.init_node('forklift_tcpip')
        communication_module = CommunicationModule()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')