#!/usr/bin/env python3

from time import sleep
import rospy as r
import os
import datetime as DT
from std_msgs.msg import Bool
from robot_dhi_1.msg import LogMessages

class LogTester:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.logToSend = LogMessages()
        
        try:
            self.logPub = r.Publisher('Forklift/state/log', LogMessages, queue_size=1, latch=True)
                
        except(r.ServiceException, r.ROSException) as e:
            r.logerr("connect/subscribers/publishers: %s" % e)
        r.loginfo('Creating log...')
        self.CreateLog()
        r.loginfo(f'Log created: {self.logToSend}')
        self.PublishLog()
        r.loginfo('log published!')
        
    def CreateLog(self):
        now = DT.datetime.now()
        self.logToSend.Date =  now.strftime('%d-%m-%Y %H:%M:%S')
        
        self.logToSend.Level = 1
        self.logToSend.Message = 'Wiadomsc testowa'
    def PublishLog(self):
        self.logPub.publish(self.logToSend)
            
                       
if __name__ == '__main__':
    try:    
        r.init_node('log_test')
        logTester = LogTester()
        r.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        r.spin()
    except (r.ServiceException, r.ROSException) as e:
        r.logerr("Main call failed: %s" % e)
        