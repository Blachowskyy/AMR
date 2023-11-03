#!/usr/bin/env python3
import subprocess
import os
import signal
import time
import rospy
import asyncio
import tf.transformations
from time import sleep
from std_msgs.msg import Bool
from geometry_msgs.msg import PoseStamped, Quaternion
from actionlib_msgs.msg import GoalStatusArray, GoalStatus
from robot_dhi_1.msg import WorkstateSelect as WS, WorkstateRead as WR
from robot_dhi_1.msg import FleetManagerCommandsIn as FmsIn, FleetManagerCommandsOut as FmsOut
from robot_dhi_1.msg import FleetManagerTaskDataIn as TaskIn, FleetManagerTaskDataOut as TaskOut

class Forklift():
    def __init__(self):
        #Zmienne odpowiadajace za uruchamianie procesow
        self.PackageFolder = 'robot_dhi_1'
        self.CommunicationFile = 'ForkliftCommunication.launch'
        self.CommunicationProcess = None
        self.AutoModeInitializationFile = 'ForkliftAutoDiagnostic.launch'
        self.AutoModeInitializationProcess = None
        self.NavigationRideABFile = 'ForkliftNavigationRide.launch'
        self.NavigationRideABProcess = None
        self.ChargingSequenceFile = 'ForkliftChargingFrequence.launch'
        self.ChargingSequenceProcess = None
        self.LoadPaletteAtMagazineFile = 'ForkliftMagazineLoad.launch'
        self.LoadPaletteAtMagazineProcess = None
        self.UnloadPaletteAtMagazineProcess = 'ForkliftMagazineUnload.launch'
        self.UnloadPaletteAtMagazineProcess = None
        self.LoadPaletteAtDestinationFile = 'ForkliftDestinationLoad.launch'
        self.LoadPaletteAtDestinationProcess = None
        self.UnloadPaletteAtDestinationFile = 'ForkliftDestinationUnload.launch'
        self.UnloadPaletteAtDestinationProcess = None
        #Zmienne stanow pracy
        self.ActualWorkstates = WR()
        self.RequestedWorkstates = WS()
        self.RequestedWorkstatesToSend = WS()
        #Zmienne komend FMS
        self.CommandsIn = FmsIn()
        self.CommandsConfirmations = FmsOut()
        #Zmienne zadan
        self.ReceivedTask = TaskIn()
        self.LastReceivedTask = TaskIn()
        self.TaskConfirmations = TaskOut()
        #Pozostale zmienne
        self.TestStatus = False
        self.IsConnectionActive = False
        self.IsDiagnosticActive = False
        self.IsNavrideActive = False
        self.IsInStandby = False
        self.IsNewTaskArrived = False
        self.Goal = PoseStamped()
        self.workstateRequestCounter = 0
        self.GoalId = 0
        self.GoalAngle = Quaternion()
        self.GoalStatusList = GoalStatusArray()
        self.GoalStatus = None
        self.Rate = rospy.Rate(1)
        #Zmienne ustawiajace stany pracy:
        while not rospy.is_shutdown():
            try:
                #ROS Subscribers
                self.DiagnosticTestSub = rospy.Subscriber('test_status', Bool, self.TestStatusCallback)
                self.ActualWorkstatesSub = rospy.Subscriber('Forklift/state/workstates/Active', WR, self.ActiveWorkstatesCallback)
                self.CommandsInSub = rospy.Subscriber('Forklift/state/FMS/receivedCommand', FmsIn, self.CommandsInCallback)
                self.ReceivedTaskSub = rospy.Subscriber('Forklift/state/FMS/Task/received',TaskIn, self.ReceivedTaskCallback)
                self.GoalStatusSub = rospy.Subscriber('move_base/status', GoalStatusArray, self.GoalStatusCallback)
                #ROS Publishers
                self.GoalPub = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=1, latch=True)
                self.RequestedWorkstatesPub = rospy.Publisher('Forklift/state/workstates/Requested', WS, queue_size=1, latch=True)
                self.TaskConfirmationsPub = rospy.Publisher('Forklift/state/FMS/Task/status', TaskOut, queue_size=1, latch=True)
            except(rospy.ServiceException, rospy.ROSException, SystemExit) as e:
                rospy.loginfo(e)
            self.MainTask()
            self.Rate.sleep()
    #Metody ustawiajace odpowiednio zadania stanow pracy
    def PublishGoal(self):
        self.Goal.header.seq = self.GoalId
        self.Goal.header.frame_id = 'map'
        self.Goal.header.stamp = rospy.Time.now()
        self.Goal.pose.position.x = self.ReceivedTask.CoordinatesX
        self.Goal.pose.position.y = self.ReceivedTask.CoordinatesY
        quaterion = tf.transformations.quaternion_from_euler(0, 0, self.ReceivedTask.CoordinatesTetha)
        self.Goal.pose.orientation.x = quaterion[0]
        self.Goal.pose.orientation.y = quaterion[1]
        self.Goal.pose.orientation.z = quaterion[2]
        self.Goal.pose.orientation.w = quaterion[3]
        self.GoalPub.publish(self.Goal)
        sleep(0.1)
        while True:
            if self.GoalStatus == 1:
                rospy.loginfo('Goal accepted')
            break;
    def GoalStatusCallback(self, msg):
        self.GoalStatus = [status.status for status in msg.status_list]
        print(self.GoalStatus)
    def TestStatusCallback(self, msg):
        self.TestStatus = msg.data
    def ActiveWorkstatesCallback(self, msg):
        self.ActualWorkstates = msg
    def CommandsInCallback(self, msg):
        self.CommandsIn = msg
    def ReceivedTaskCallback(self, msg):
        self.ReceivedTask - msg
        if self.ReceivedTask != self.LastReceivedTask:
            self.IsNewTaskArrived = True
            self.LastReceivedTask = self.ReceivedTask
    def MainTask(self):
        rospy.loginfo('===========Starting forklift launcher selector===========')
        checker = self.LaunchCommunication()
        if checker:
            self.AwaitForModeSelect()
    def LaunchCommunication(self):
        while not self.IsConnectionActive:
            rospy.loginfo("Communication launcher: NOT WORKING")
            self.CommunicationProcess = subprocess.Popen(['roslaunch', self.PackageFolder, self.CommunicationFile])
            sleep(2)
            if self.CommunicationProcess.poll() is None:
                rospy.loginfo('Communication launcher: Problem at launching, retrying...')
                self.IsConnectionActive = False
                self.CommunicationProcess.terminate()
                self.CommunicationProcess.wait()
                sleep(10)
            else:
                rospy.loginfo('Communication launcher: Communication module active!')
                self.IsConnectionActive = True
            if self.IsConnectionActive:
                return self.IsConnectionActive;
        if self.IsConnectionActive:
            if self.CommunicationProcess.poll() is None:
                self.IsConnectionActive = False
                rospy.loginfo('Communication Module: Stopped working')
                return self.IsConnectionActive
            else:  
                rospy.loginfo('Communication launcher: ALREADY RUNNING')
                return self.IsConnectionActive
    def AwaitForModeSelect(self):
        rospy.loginfo('Mode Selector: Starting....')
        
        selectAutoMode = self.CommandsIn.InitializeAutoMode
        selectManualMode = self.CommandsIn.ManualModeOverride or self.ActualWorkstates.S0_3
        if selectManualMode:
                selectAutoMode = False
        if selectManualMode:
            self.ManualMode()
        if selectAutoMode:
            self.AutoModeMainModule()
    def InitializeDiagnostic(self):
        rospy.loginfo('Auto Mode - Diagnostic: STARTING....')
        retryCounter = 0
        self.AutoModeInitializationProcess = subprocess.Popen(['roslaunch', self.PackageFolder, self.AutoModeInitializationFile])
        sleep(3)
        rospy.loginfo('Auto Mode - Diagnostic: Checking is process active')
        while retryCounter <= 3 and not self.IsDiagnosticActive:
            if (self.AutoModeInitializationProcess.poll() is None):
                self.IsDiagnosticActive = False
                retryCounter += 1
            else:
                self.IsDiagnosticActive = True
                rospy.loginfo('Auto Mode - Diagnostic: is running...')
                break;
            if retryCounter > 3:
                self.IsDiagnosticActive = False
                rospy.loginfo('Auto Mode - Diagnostic: Problem in launching file...')
                break;
        while self.IsDiagnosticActive:
            timeout = 30
            retryCounter = 20
            rospy.loginfo(f'Auto Mode - Diagnostic: Waiting for test passed, checking every {timeout} seconds..')
            sleep(timeout)
            if (self.TestStatus):
                rospy.loginfo('Auto Mode - Diagnostic: Test passed. Setting auto mode in standby')
                break;
            if (not self.TestStatus):
                rospy.loginfo('Auto Mode - Diagnostic: timeout loop')
                retryCounter -= 1
                timeleft = (timeout * retryCounter) / 60
                rospy.loginfo(f'Auto Mode - Diagnostic: time left for passing the test: {timeleft} minutes')
            if (retryCounter <= 0):
                rospy.loginfo('Auto Mode - Diagnostic: Test not passed - timeout error!')
                break;
        rospy.loginfo('Auto Mode - Diagnostic: Trying close process started. SHUTTING DOWN')
        self.AutoModeInitializationProcess.terminate()
        self.AutoModeInitializationProcess.wait(timeout=20)
        if self.AutoModeInitializationProcess.poll is not None:
            rospy.loginfo('Auto Mode - Diagnostic: There was a problem with shutting proces - trying to kill now')
            self.AutoModeInitializationProcess.kill()
            self.AutoModeInitializationProcess.wait(timeout=20)
            if self.AutoModeInitializationProcess.poll() is not None:
                rospy.loginfo('Auto Mode - Diagnostic: Problem with killing process')
        if self.AutoModeInitializationProcess.poll() is None:
            self.IsDiagnosticActive = False
            rospy.loginfo('Auto Mode - Diagnostic: SHUTTED DOWN!')
    def SetAutoMode(self):
        rospy.loginfo('Auto Mode - Setting auto mode started...')
        self.RequestedWorkstates = WS()
        self.RequestedWorkstates.IniDiagCompleted = True
        self.RequestedWorkstatesPub.publish(self.RequestedWorkstates)
        sleep(1)
        while True:
            if self.ActualWorkstates.S2 and self.ActualWorkstates.S3 and self.ActualWorkstates.S4:
                rospy.loginfo('Auto mode - confirmation!')
                break;
            rospy.loginfo('Wating for auto mode setting')
    def SelectWorkType(self):
        rospy.loginfo('Auto mode - selecting accurate work type started...')
    def AutoModeNavigationRide(self):
        rospy.loginfo('Auto Mode - Navigation Ride: Starting....')
        rospy.loginfo('Publishing goal and starting ride')
        self.PublishGoal()
        while not self.TaskConfirmations.IsDone and self.TaskConfirmations.IsRunning:
            if self.GoalStatus[0] == 3:
                self.TaskConfirmations.IsRunning = False
                self.TaskConfirmations.IsDone = True
                self.TaskConfirmationsPub.publish(self.TaskConfirmations)
                sleep(0.1)
                rospy.loginfo('============Goal reached!===============')
                break
            if self.CommandsIn.CancelLastTask:
                self.CommandsConfirmations.ConfirmCancelLastTask = True
    def AutoModeMainModule(self):
        rospy.loginfo('Auto Mode - Main Program: Starting...')
        self.InitializeDiagnostic()
        if not self.IsDiagnosticActive:
            self.SetAutoMode()
            while self.ActualWorkstates.S2 and self.ActualWorkstates.S3 and self.ActualWorkstates.S4:
                if self.ActualWorkstates.S4_0:
                    while self.IsNewTaskArrived:
                        rospy.loginfo('New task arrived! Setting accurate launcher!')
                        if self.ReceivedTask.TaskType == 2:
                            rospy.loginfo('Choosen Ride from point A to B. Starting now')
                            self.RequestedWorkstates = WS()
                            self.RequestedWorkstates.StartNavride
                            self.RequestedWorkstatesPub.publish(self.RequestedWorkstates)
                            sleep(1)
                            while True:
                                if self.ActualWorkstates.S4_1:
                                    rospy.loginfo('PLC accepted request')
                                    break;
                                rospy.loginfo('Waiting for PLC to accept request')
                            while self.ActualWorkstates.S4_1:
                                self.NavigationRideABProcess = subprocess.Popen(['roslaunch', self.PackageFolder, self.NavigationRideABFile])
                                sleep(2)
                                if self.NavigationRideABProcess.poll() is None:
                                    self.IsNavrideActive = False;
                                else:
                                    self.IsNavrideActive = True;
                                    break;
                                if self.IsNavrideActive:
                                    rospy.loginfo('Launched ride process!')
                                    break
                            while self.IsNavrideActive:
                                rospy.loginfo('Waiting for start command...')
                                if self.CommandsIn.StartTask:
                                    break;
                                sleep(1) 
                            while self.IsNavrideActive and self.CommandsIn.StartTask:
                                self.CommandsConfirmations.ConfirmStartTask = True
                                self.TaskConfirmations.IsRunning = True
                                self.AutoModeNavigationRide()
    def ManualMode(self):
        rospy.loginfo('Manual Mode - Main Program: Starting.....')
        if (self.ActualWorkstates.S0_1 and not self.ActualWorkstates.S0_3):
            self.RequestedWorkstates = WS()
            self.RequestedWorkstates.ManualModeFromFMS = True
            while self.workstateRequestCounter < 3:
                if self.ActualWorkstates.S0_3:
                    self.workstateRequestCounter = 0
                    rospy.loginfo('Manual Mode: Selection OK!')
                    break;
                if self.workstateRequestCounter > 3:
                    self.workstateRequestCounter = 0
                    rospy.loginfo('Manual Mode: Error when selecting workstate')
                sleep(1)
                self.workstateRequestCounter += 1
            while self.ActualWorkstates.S0_3:
                timeout = 3
                rospy.loginfo(f'Manual Mode: Active - checking every {timeout} seconds for change')
                sleep(timeout)
                if (not self.CommandsIn.ManualModeOverride and self.CommandsIn.InitializeAutoMode):
                    rospy.loginfo('Manual Mode: Interrupted by FMS - selecting auto mode')
                    break;
                # tu dolozyc sprawdzenie selektora trybu na wozku          
    
if __name__ == '__main__':
    try:
        roscore_running = False
        try:
            rospy.loginfo('=========Checking for roscore running========')
            subprocess.check_output(['pgrep', '-x', 'roscore'])
            roscore_running = True
            rospy.loginfo('=========Roscore arleady running=========')
        except Exception:
            pass
        if not roscore_running:
            rospy.loginfo("========Starting ROSCORE=========")
            roscore_process = subprocess.Popen(['roscore'])
            time.sleep(5)
        rospy.init_node('ForkliftLauncherSelector')
        forklift = Forklift()
        rospy.spin()
    except (rospy.ROSException) as e:
        rospy.logdebug_once(e)
    finally:
        print("============ SHUTDOWN ===========")
        os.kill(roscore_process.pid, signal.SIGINT)
        roscore_process.wait()