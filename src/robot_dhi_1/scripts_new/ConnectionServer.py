#!/usr/bin/env python3
import os
import socket
from time import sleep
import rospy
from std_msgs.msg import Int64, Float32, Bool, String
from geometry_msgs.msg import Pose2D
from robot_dhi_1.msg import FlexiReads, WorkstateRead, TaskMessages, FleetMenagerCommands
import struct
import datetime


class CommunicationModule:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.server_address = ('192.168.1.13', 8000)
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
        self.receivedData = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rate = rospy.Rate(5)
        self.currentLocMessage = ''
        self.activeWorkstate = WorkstateRead()
        self.safetyStatus = FlexiReads()
        self.lidarlocPose = Pose2D()
        self.taskReceived = TaskMessages()
        self.FMC = FleetMenagerCommands()
        self.FMCconfirmations = FleetMenagerCommands()
        self.activeTask = 'start'
        self.queuedTasks = 'start'
        self.sock.settimeout(10.0)
    
        self.startup = True
        rospy.loginfo('connecting to: %s port %s' %self.server_address)
        while not rospy.is_shutdown():
            try:
                self.sock.connect(self.server_address)
                self.battery_voltage_sub = rospy.Subscriber('Forklift/state/battery_voltage', Float32, self.battery_voltage_read)
                self.battery_percentage_sub = rospy.Subscriber('Forklift/state/battery_percentage', Float32, self.battery_percentage_read)
                self.battery_critical_sub = rospy.Subscriber('Forklift/state/battery_critical_state', Bool, self.battery_critical_read)
                self.encoder_speed_sub = rospy.Subscriber('PLC/read/encoder_speed', Int64, self.encoder_speed_read)
                self.servo_angle_sub = rospy.Subscriber('Forklift/drive/current_servo_angle', Float32, self.servo_angle_read)
                self.forkliftLocalizationSub = rospy.Subscriber('sickLidarPose2D', Pose2D, self.currentLocRead)
                self.safetyStatusSub = rospy.Subscriber('Forklift/state/safety/safety_status', FlexiReads, self.safetyRead)
                self.activeWorkstatesSub = rospy.Subscriber('Forklift/state/workstates/PLC_active', WorkstateRead, self.activeWorkstateRead)
                self.cargoWeightSub = rospy.Subscriber('Forklift/forks/cargo_weight', Int64, self.cargoWeightRead)
                self.currentForkHeightSub = rospy.Subscriber('Forklift/forks/forks_height', Int64, self.forkHeightRead)
                self.currentPwmSub = rospy.Subscriber('Forklift/control/PWM_curtis', Int64, self.currentPWMRead)
                self.confirmCommandsSub = rospy.Subscriber('Forklift/state/WMS/confirmCommand', FleetMenagerCommands, self.confirmationCommandsCallback)
                self.activeTaskSub = rospy.Subscriber('Forklift/state/WMS/activeTask', TaskMessages, self.activeTaskCallback)
                self.queuedTaskSub = rospy.Subscriber('Forklift/state/WMS/queuedTasks', String, self.queuedTasksCallback)
                self.receivedTaskPub = rospy.Publisher('Forklift/state/WMS/receivedTask', TaskMessages, queue_size=1)
                self.receivedCommandsPub = rospy.Publisher('Forklift/state/WMS/receivedCommand', FleetMenagerCommands, queue_size=1)
            except(rospy.ServiceException, rospy.ROSException, socket.error) as e:
                self.log_level = 4
                self.log_message = str(e)
                
            self.communication()
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
        self.battery_voltage = str(round(data, 2))
    def battery_percentage_read(self, msg):
        data = msg.data
        self.battery_percentage = str(round(data, 2))
    def battery_critical_read(self, msg):
        data = msg.data
        self.battery_critical = str(round(data, 2))
    def encoder_speed_read(self, msg):
        data = msg.data
        self.speed_actual = str(round((data / 100), 2))
    def createDataList(self):
        self.sendData.append(self.battery_voltage)
        self.sendData.append(self.battery_percentage)
        self.sendData.append(self.battery_critical)
        self.sendData.append(self.speed_actual)
        self.sendData.append(self.servo_angle)
        self.sendData.append(self.currentPwm)
        self.sendData.append(self.forksHeight)
        self.sendData.append(self.cargoWeight)
        self.sendData.append(self.lidarlocPose.x)
        self.sendData.append(self.lidarlocPose.y)
        self.sendData.append(round(self.lidarlocPose.theta, 3))
        self.sendData.append(self.activeWorkstate.S0_1)
        self.sendData.append(self.activeWorkstate.S0_2)
        self.sendData.append(self.activeWorkstate.S0_3)
        self.sendData.append(self.activeWorkstate.S1)
        self.sendData.append(self.activeWorkstate.S4)
        self.sendData.append(self.safetyStatus.LeftScannerEmergencyZoneStatus)
        self.sendData.append(self.safetyStatus.LeftScannerSoftStopZoneStatus)
        self.sendData.append(self.safetyStatus.LeftScannerReducedSpeedZoneStatus)
        self.sendData.append(self.safetyStatus.RightScannerEmergencyZoneStatus)
        self.sendData.append(self.safetyStatus.RightScannerSoftStopZoneStatus)
        self.sendData.append(self.safetyStatus.RightScannerReducedSpeedZoneStatus)
        tmp = not self.safetyStatus.LeftScannerDeviceError and not self.safetyStatus.LeftScannerDeviceError and not self.safetyStatus.LeftScannerContaminationError and not self.safetyStatus.LeftScannerMonitoringCaseValid
        self.sendData.append(tmp)
        tmp = not self.safetyStatus.RightScannerDeviceError and not self.safetyStatus.RightScannerDeviceError and not self.safetyStatus.RightScannerContaminationError and not self.safetyStatus.RightScannerMonitoringCaseValid
        self.sendData.append(tmp)
        self.sendData.append(self.safetyStatus.EncoderOK)
        self.sendData.append(self.safetyStatus.CpuOK)
        self.sendData.append(self.safetyStatus.Standstill)
        # self.noneTypeToFalse()b
        self.sendData.append(self.FMCconfirmations.confirmEmergencyStopForklift)
        self.sendData.append(self.FMCconfirmations.confirmStopForklift)
        self.sendData.append(self.FMCconfirmations.confirmReset)
        self.sendData.append(self.FMCconfirmations.continuework)
        self.sendData.append(self.FMCconfirmations.confirmManualModeOverride)
        self.sendData.append(self.FMCconfirmations.confirmCancelLastTask)
        self.sendData.append('&')
        self.createTasksList()
        # Przekształć każdy element w liście na string i zastąp oryginalną listę nową listą zawierającą stringi
        self.sendData = [str(item) if item is not None else '0' for item in self.sendData]
    def createTasksList(self):
        if self.activeTask is None:
            self.activeTask = 'No active job now'
        if self.queuedTasks is None:
            self.queuedTasks = 'Task queue is empty'
        self.sendData.append(self.activeTask)
        self.sendData.append(self.queuedTasks)
        # self.sendData.append(len(self.sendData))
        # self.sendData.append('&')
        
    def clearData(self):
        self.sendData.clear()
        self.bytes_to_send = ''
        # self.activeTask = ''
        # self.queuedTasks = ''
        self.receivedData.clear()
    def convertSendData(self):
        for item in self.sendData:
            self.bytes_to_send = self.bytes_to_send + item + '#'
        # print(self.bytes_to_send)       
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
            # rospy.loginfo('Sending "%s"' % message)
            self.sock.send(message)
            # self.clearData()
            self.receive_bytes()
            # rospy.loginfo("TU")
        except BrokenPipeError:
            rospy.logerr('Broken pipe error, reconnecting...')
            self.reconnect_socket()
    def reconnect_socket(self):
        self.sock.close()
        self.sock = None
        while self.sock is None:
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect(self.server_address)
                
                rospy.loginfo('Successfully reconnected.')
            except (rospy.ServiceException, rospy.ROSException, socket.error) as e:
                rospy.logerr("Reconnection failed: %s. Retrying in 10 seconds..." % e)
    def publishReceivedTask(self):
        self.taskReceived.TaskID = str(self.receivedData[0])
        self.taskReceived.TaskType = int(self.receivedData[1])
        self.taskReceived.TaskDate = str(datetime.datetime.now())
        self.taskReceived.CoordinatesX = float(self.receivedData[2])
        self.taskReceived.CoordinatesY = float(self.receivedData[3])
        self.taskReceived.CoordinatesTetha = float(self.receivedData[4])
        self.taskReceived.ImportanceLevel = int(self.receivedData[5])
        self.receivedTaskPub.publish(self.taskReceived)
        # print(self.taskReceived)
    def publishFleetMenagerCommand(self):
        if (self.receivedData[6] == 'False'):
            self.FMC.cancelLastTask = False
        elif(self.receivedData[6] == 'True'):
            self.FMC.cancelLastTask = True
        else:
            self.FMC.cancelLastTask = None
        self.receivedCommandsPub.publish(self.FMC)
        print(self.FMC)
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
            print(data_string)
            split_data = data_string.split('#')  # dzielenie na listę
            # print(len(split_data))
            if len(split_data[0]) > 5:
                for item in split_data:
                    self.receivedData.append(item)
                print(split_data)
                rospy.loginfo(type(self.receivedData[0]))
                self.publishReceivedTask()
                self.publishFleetMenagerCommand()                
        except (BrokenPipeError, socket.error):
            rospy.logerr('Broken pipe error, reconnecting...')
            self.reconnect_socket()
    def communication(self):
        # os.system('clear')
        create_check = self.create_bytes_to_send()
        if create_check and not self.startup:
            self.send_bytes()
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