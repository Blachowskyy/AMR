#!/usr/bin/env python3

import threading
import os
from time import sleep
from pyModbusTCP import client
import rospy
from std_msgs.msg import Int64, Float32, Bool, Int64MultiArray
from sensor_msgs import point_cloud2
from sensor_msgs.msg import PointCloud2
from sensor_msgs.msg import PointField
from std_msgs.msg import Header
from robot_dhi_1.msg import Scangrids
import math
import numpy as np
from tf.msg import tfMessage
import geometry_msgs.msg
import sensor_msgs.msg
import tf
import tf2_ros


class LidarToPointCloud:
    def __init__(self):
        self.Scangrid2R = [0] * 32
        self.Scangrid2L = Int64MultiArray()
        self.ScangridMerged = [0] * 64
        self.ScangridData = Scangrids()
        self.rate = rospy.Rate(10)  # 10Hz
    
        while not rospy.is_shutdown():
            try:
                self.scangrid1ranges_sub = rospy.Subscriber('PLC/read/scangrid1ranges', Int64MultiArray, self.scangrid1ranges_callback)
                self.scangrid2ranges_sub = rospy.Subscriber('PLC/read/scangrid2ranges', Int64MultiArray, self.scangrid2ranges_callback)
                self.scangridMerged_pub = rospy.Publisher('PLC/read/scangrid_merged', PointCloud2, queue_size=1, latch=True)
                self.ScangridDataPub = rospy.Publisher('Forklift/Scangrids/DataOut', Scangrids,queue_size=1, latch=True)
            except (rospy.ROSException):
                rospy.loginfo('error')
                

    def scangrid1ranges_callback(self, msg):
        data = msg.data
        for i in range (len(data)):
            self.Scangrid2R[i] = data[i] / 1000
    def scangrid2ranges_callback(self, msg):
        self.Scangrid2L = msg
        self.ScangridData.LeftScanner.Range0 = self.Scangrid2L.data[0]
        self.ScangridData.LeftScanner.Range1 = self.Scangrid2L.data[1]
        self.ScangridData.LeftScanner.Range2 = self.Scangrid2L.data[2]
        self.ScangridData.LeftScanner.Range3 = self.Scangrid2L.data[3]
        self.ScangridData.LeftScanner.Range4 = self.Scangrid2L.data[4]
        self.ScangridData.LeftScanner.Range5 = self.Scangrid2L.data[5]
        self.ScangridData.LeftScanner.Range6 = self.Scangrid2L.data[6]
        self.ScangridData.LeftScanner.Range7 = self.Scangrid2L.data[7]
        self.ScangridData.LeftScanner.Range8 = self.Scangrid2L.data[8]
        self.ScangridData.LeftScanner.Range9 = self.Scangrid2L.data[9]
        self.ScangridData.LeftScanner.Range10 = self.Scangrid2L.data[10]
        self.ScangridData.LeftScanner.Range11 = self.Scangrid2L.data[11]
        self.ScangridData.LeftScanner.Range12 = self.Scangrid2L.data[12]
        self.ScangridData.LeftScanner.Range13= self.Scangrid2L.data[13]
        self.ScangridData.LeftScanner.Range14= self.Scangrid2L.data[14]
        self.ScangridData.LeftScanner.Range15 = self.Scangrid2L.data[15]
        self.ScangridData.LeftScanner.Range16 = self.Scangrid2L.data[16]
        self.ScangridData.LeftScanner.Range17 = self.Scangrid2L.data[17]
        self.ScangridData.LeftScanner.Range18 = self.Scangrid2L.data[18]
        self.ScangridData.LeftScanner.Range19 = self.Scangrid2L.data[19]
        self.ScangridData.LeftScanner.Range20 = self.Scangrid2L.data[20]
        self.ScangridData.LeftScanner.Range21 = self.Scangrid2L.data[21]
        self.ScangridData.LeftScanner.Range22 = self.Scangrid2L.data[22]
        self.ScangridData.LeftScanner.Range23 = self.Scangrid2L.data[23]
        self.ScangridData.LeftScanner.Range24 = self.Scangrid2L.data[24]
        self.ScangridData.LeftScanner.Range25 = self.Scangrid2L.data[25]
        self.ScangridData.LeftScanner.Range26 = self.Scangrid2L.data[26]
        self.ScangridData.LeftScanner.Range27 = self.Scangrid2L.data[27]
        self.ScangridData.LeftScanner.Range28 = self.Scangrid2L.data[28]
        self.ScangridData.LeftScanner.Range29 = self.Scangrid2L.data[29]
        self.ScangridData.LeftScanner.Range30 = self.Scangrid2L.data[30]
        self.ScangridDataPub.publish(self.ScangridData)
        print(self.ScangridData.LeftScanner)
        sleep(0.1)
        
        
        
    
if __name__ == '__main__':
    try:
        rospy.init_node('lidar_to_point_cloud')
    
        lidar_to_point_cloud = LidarToPointCloud()
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
