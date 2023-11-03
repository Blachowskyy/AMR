#!/usr/bin/env python3
import rospy
import datetime
from rosgraph_msgs.msg import Log
from robot_dhi_1.msg import LogMessages
class LogCatcher:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.ReceivedLog = Log()
        self.LastReceivedLog = Log()
        self.RobotLogMessage = LogMessages()
        self.Rate = rospy.Rate(1)
        while not rospy.is_shutdown():
            try:
                rosoutSub = rospy.Subscriber('rosout_agg', Log, self.RosoutAggCallback)
                self.logPub = rospy.Publisher('Forklift/state/log', LogMessages, queue_size=1, latch=True)
                    
            except(rospy.ServiceException, rospy.ROSException) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
        
    def RosoutAggCallback(self, msg):
        self.ReceivedLog = msg
        if self.ReceivedLog.header.seq != self.LastReceivedLog.header.seq:
            if self.ReceivedLog.level > 2:
                self.RobotLogMessage.Level = self.ReceivedLog.level
                self.RobotLogMessage.Message = self.ReceivedLog.msg
                self.RobotLogMessage.Date = datetime.datetime.now()
                self.logPub.publish(self.RobotLogMessage)
            if self.ReceivedLog.level <= 2:
                print(f'Received new log under the minimal level: {self.ReceivedLog.level}')
            self.LastReceivedLog = self.ReceivedLog
        
        self.Rate.sleep()
if __name__ == '__main__':
    try:    
        rospy.init_node('RosLogCatchingServiceNode')
        logCatcher = LogCatcher()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        