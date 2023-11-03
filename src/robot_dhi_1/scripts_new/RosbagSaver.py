#!/usr/bin/env python3
import rospy
import subprocess
import datetime
import rosbag
import os
from time import sleep
from std_msgs.msg import Int64, Float32
class RosbagMonitor:
    def __init__(self):
        rospy.loginfo('=========BATTERY MONITRO STARTED=======')
        self.BatteryPercentage = Int64()
        self.BatteryVoltage = Float32()
        
        while not rospy.is_shutdown():
            try: 
                self.BatteryVoltageSub = rospy.Subscriber('Forklift/state/battery_voltage', Float32, self.BatteryVoltageCallback)
                self.BatteryPercentageSub = rospy.Subscriber('Forklift/state/battery_percentage',Int64, self.BatteryPercentageCallback)
            except (rospy.ROSInternalException, rospy.ROSException) as e:
                rospy.loginfo(e)
            self.CreateRosbag()        
    def CreateRosbag(self):
        rospy.loginfo('Creating new rosbag file')
        currentTime = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M:%S')
        bagName = os.path.join('ROSBAG', 'batteryTestData:{}.bag'.format(currentTime))
        if not os.path.exists(os.path.dirname(bagName)):
            os.makedirs(os.path.dirname(bagName))
        bag = rosbag.Bag(bagName, 'w')
        rate = rospy.Rate(10)
        while True:
            criticalbattery = Int64()
            criticalbattery = int(str(self.BatteryPercentage.data))
            if self.BatteryVoltage is not None:
                message = Float32()
                message.data = self.BatteryPercentage
                bag.write('Forklift/state/battery_voltage', message.data, rospy.Time.now())
            if self.BatteryPercentage is not None:
                message = Int64()
                message.data = self.BatteryPercentage
                bag.write('Forklift/state/battery_percentage', message.data, rospy.Time.now())
                if message.data.data >= 1:
                    bag.close()
                    rospy.loginfo(message.data)
                    rospy.loginfo('Napęcie baterii spadło poniżej krytycznego poziomu, zamykam plik rosbag w celu archiwizacji danych...')    
                    break
            # if self.BatteryPercentage >= 1:
            #     bag.close()
            #     rospy.loginfo(criticalbattery)
            #     rospy.loginfo('Napęcie baterii spadło poniżej krytycznego poziomu, zamykam plik rosbag w celu archiwizacji danych...')    
            #     break
            rate.sleep()
            print('Nothing happened. Taking a little nap... :)')
    def BatteryVoltageCallback(self, msg):
        self.BatteryVoltage = msg.data
    def BatteryPercentageCallback(self, msg):
        self.BatteryPercentage = msg.data

    
                    
if __name__ == '__main__':
    try:
        rospy.init_node('RosbagSaver')
        
        test = RosbagMonitor()
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')















