#!/usr/bin/env python3

from time import sleep
import rospy as r
import os
from std_msgs.msg import Bool
from robot_dhi_1.msg import WorkstateRead as WR, WorkstateSelect as WS


class WorkstateSelector:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.workstate_out = WS()
        self.workstate_out_last = WS()
        self.workstate_actual = WR()
        self.selected_workstate = WS()
        self.Send_Table = [0] * 16
        self.Read_Table = [0] * 16
        self.selected_workstate_old = 0
        self.workstate_ok = True
        self.wrokstate_selector_status = False
        self.work = False
        self.rate = r.Rate(10)
        self.data_changed = True
        self.clear = lambda: os.system('clear')
        while not r.is_shutdown():
            try:
                self.worsktate_state_pub = r.Publisher('Forklift/state/workstate_status', Bool, queue_size=1)
                self.worsktate_pub = r.Publisher('Forklift/state/workstates/PLC_requested_by_selector', WS, queue_size=1)
                
                self.worsktate_receiver = r.Subscriber('Forklift/control/select_workstate', WS, self.workstate_selected_read, queue_size=1)
                self.worsktate_sub = r.Subscriber('Forklift/state/workstates/PLC_active', WR, self.workstate_actual_read)
                
            except(r.ServiceException, r.ROSException) as e:
                r.logerr("connect/subscribers/publishers: %s" % e)
            if self.data_changed:
                self.workstate_main()
            self.rate.sleep()
        
    def workstate_actual_read(self, msg):
        self.workstate_actual = msg
    def workstate_selected_read(self, msg):
        self.selected_workstate = msg
    def WorkstateValidation(self):
        if self.selected_workstate.AutoMode:
            if self.workstate_actual.S1:
                self.workstate_ok = True
            else:
                self.workstate_ok = False
        if self.selected_workstate.IniDiagCompleted:
            if self.workstate_actual.S2 and self.workstate_actual.S3 and self.workstate_actual.S4 and self.workstate_actual.S4_0:
                self.workstate_ok = True
            else:
                self.workstate_ok = False
        if self.selected_workstate.StartNavride:
            if self.workstate_actual.S4_1:
                self.workstate_ok = True
            else:
                self.workstate_ok = False
        r.loginfo(self.workstate_ok)        
    def workstate_main(self):
            self.selected_workstate.StartNavride = True
            # self.selected_workstate.IniDiagCompleted=True
            self.workstate_out = self.selected_workstate
            r.loginfo(self.workstate_out)
            self.worsktate_pub.publish(self.workstate_out)
            sleep(0.1)
            self.WorkstateValidation()
            self.worsktate_state_pub.publish(self.workstate_ok)
            if not self.workstate_ok:
                r.loginfo('WAIT FOR COMMAND READY')
            self.workstate_out_last = self.workstate_out
            
            # self.clear()
            
            
                       
if __name__ == '__main__':
    try:    
        r.init_node('forklift_workstate_selector')
        workstate_selector = WorkstateSelector()
        r.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        r.spin()
    except (r.ServiceException, r.ROSException) as e:
        r.logerr("Main call failed: %s" % e)
        