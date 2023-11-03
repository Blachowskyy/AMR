#!/usr/bin/env python3
import subprocess
import os
import signal
import time
import rospy
from time import sleep
from std_msgs.msg import Bool, ByteMultiArray
from robot_dhi_1.msg import WorkstateSelect, WorkstateRead

class Forklift():
    def __init__(self):
        self.WorkstateSet = WorkstateSelect()
        self.WorkstateActive = WorkstateRead()
        self.communication_file = 'forklift_communication.launch'
        self.communication_process = None
        self.communication_active = False
        self.diagnostic_file = 'forklift_diagnostic.launch'
        self.diagnostic_process = None
        self.diagnostic_active = False
        self.navride_file = 'robot_dhi.launch'
        self.navride_process = None
        self.navride_active = False
        self.auto_mode = False
        self.auto_mode_active_launch = None
        self.auto_mode_active_process = None
        self.package = 'robot_dhi_1'
        self.test_status = None
        self.navride = 1
        self.login_status = False
        self.login_flag = False
        self.auto_mode_button = False
        self.first_run = True
        # self.start_roscore()
        rospy.init_node('forklift_main')
        while not rospy.is_shutdown():
            self.test_sub = rospy.Subscriber('test_status', Bool, self.test_status_read)
            self.operator_status = rospy.Subscriber('Forklift/state/user/login_status', Bool,self.login_status_callback)
            self.auto_mode_button_sub = rospy.Subscriber('Forklift/state/user/reinitialise_auto', Bool, self.auto_mode_button_callback)
            self.worsktate_sub = rospy.Subscriber('Forklift/state/workstates/PLC_Active', WorkstateRead, self.workstate_current_read)
            self.workstate_pub = rospy.Publisher('Forklift/control/select_workstate', WorkstateSelect, queue_size=1)
            self.forklift_main()
            if not self.test_status:
                break
    def workstate_current_read(self, msg):
        self.WorkstateActive = msg
    def auto_mode_button_callback(self, msg):
        self.auto_mode_button = msg.data
    def login_status_callback(self, msg):
        self.login_status = msg.data
        if self.login_status:
            self.login_flag = True
        while self.login_flag :
            sleep(30)
            self.login_flag = False
            break
            
    def test_status_read(self, msg):
        self.test_status = msg.data
    def forklift_main(self):
        while not self.communication_active:
            rospy.loginfo("Starting forklift communication module...")   
            self.communication_process = subprocess.Popen(['roslaunch', self.package, self.communication_file])
            if self.communication_process != None:
                self.communication_active = True
                rospy.loginfo("Communication module started") 
                sleep(2)
            else:
                self.communication_process = False
                rospy.loginfo("Communication module error!") 
                sleep(2)
        while self.communication_active:
            rospy.loginfo("Checking for auto mode confirmation....") 
            while self.login_flag or self.auto_mode_button:
                rospy.loginfo("Starting auto mode initialization diagnostic...") 
                if not self.first_run:
                    rospy.loginfo("Setting reinitialize auto mode confirmation...") 
                    self.WorkstateSet.AutoMode = False
                    self.WorkstateSet.ReinitializeAutoMode = True
                if self.first_run:
                    rospy.loginfo("Setting first cycle confirmation...") 
                    self.first_run = False
                    self.WorkstateSet.AutoMode = True
                    self.WorkstateSet.ReinitializeAutoMode = False
                self.workstate_pub.publish(self.WorkstateSet)
                print(self.diagnostic_active)
                print(self.login_flag)
                print(self.test_status)
                sleep(5)
                if not self.diagnostic_active and self.test_status == None:
                    rospy.loginfo_once('Starting diagnostic process....')
                    self.diagnostic_process = subprocess.Popen(['roslaunch', self.package, self.diagnostic_file])
                    if self.diagnostic_process != None :
                        self.diagnostic_active = True
                        print('diagnostic started')
                        sleep(2)
                    else:
                        self.diagnostic_active = False
                    if self.diagnostic_active:
                        sleep(70)
                        if not self.test_status:
                            self.diagnostic_process.kill()
                            self.diagnostic_process.wait()
                            self.diagnostic_active = False
                            rospy.loginfo_once('Test failed')
                        elif self.test_status == None:
                            rospy.loginfo_once('Waiting for test result')
                            sleep(30)
                        elif self.test_status:
                            rospy.loginfo_once('Test passed')
                            self.diagnostic_process.kill()
                            self.diagnostic_process.wait()
                            self.diagnostic_active = False
                            rospy.loginfo_once('Starting auto mode...')
                            self.auto_mode = True
                            return self.auto_mode
                    if not self.diagnostic_active and not self.test_status:
                        print('Test failed')
                        return False
               
            while not self.diagnostic_active and self.auto_mode and self.test_status and not self.login_status:
                rospy.loginfo("Confirming test passed to forklift..") 
                self.WorkstateSet.ReinitializeAutoMode = False
                self.WorkstateSet.AutoMode = False
                self.WorkstateSet.IniDiagCompleted = True
                self.workstate_pub.publish(self.WorkstateSet)
                sleep(5)
                rospy.loginfo("Starting forklift navigation riding module...") 
                self.WorkstateSet.ReinitializeAutoMode = False
                self.WorkstateSet.AutoMode = False
                self.WorkstateSet.IniDiagCompleted = False
                self.WorkstateSet.StartNavride = True
                self.workstate_pub.publish(self.WorkstateSet)
                if self.navride:
                    self.auto_mode_active_launch = self.navride_file
                    self.auto_mode_active_process = subprocess.Popen(['roslaunch', self.package, self.auto_mode_active_launch])
                if self.login_status == True:
                        self.auto_mode_active_process.kill
                self.auto_mode_active_process.wait()
                self.auto_mode_active_process = None
                if self.auto_mode_active_process == None:
                    return None
            while not self.login_status:
                time.sleep(5)
                rospy.loginfo("Waiting for user login and mode initialization...") 
                break
            
if __name__ == '__main__':
    try:
        roscore_running = False
        try:
            subprocess.check_output(['pgrep', '-x', 'roscore'])
            roscore_running = True
        except Exception:
            pass
        if not roscore_running:
            print("URUCHAMIAM ROSCORE...")
            roscore_process = subprocess.Popen(['roscore'])
            time.sleep(5)
            
        forklift = Forklift()
        rospy.spin()
    except (rospy.ROSException) as e:
        rospy.logdebug_once(e)
    finally:
        print("ROSCORE SHUTDOWN")
        os.kill(roscore_process.pid, signal.SIGINT)
        roscore_process.wait()