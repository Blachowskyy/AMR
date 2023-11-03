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
import math
import numpy as np

class LidarToPointCloud:
        def __init__(self):
            self.Scangrid2R = [0] * 32
            self.Scangrid2L = [0] * 32
            self.ScangridMerged = [0] * 64
            self.rate = rospy.Rate(10) # 10Hz

            while not rospy.is_shutdown():
                try:
                    self.scangrid1ranges_sub = rospy.Subscriber('PLC/read/scangrid1ranges', Int64MultiArray, self.scangrid1ranges_callback)
                    self.scangrid2ranges_sub = rospy.Subscriber('PLC/read/scangrid2ranges', Int64MultiArray, self.scangrid2ranges_callback)
                    self.scangridMerged_pub = rospy.Publisher('PLC/read/scangrid_merged', PointCloud2, queue_size=1)
                   
                    
                except(rospy.ServiceException, rospy.ROSException) as e:
                    rospy.logerr("connect/subscribers/publishers: %s" % e)
                
                self.Communication()

        def scangrid1ranges_callback(self,msg):
             self.Scangrid2L = msg.data

        def scangrid2ranges_callback(self,msg):
             self.Scangrid2R = msg.data


        def ScangridsSender(self):

            # TO DO: odpowiednia konwersja wspolrzednych przed zamiana ich w PointCloud2 taka, aby mialo to sens w RVIZ , na razie wszystko jest wzgledem srodka kazego z lidarow
            # czy tu chodzi o przesuniecie o pole sensor_1_to_scan_broadcasater i sensor_2_to_scan_broadcaster z tf_test.launch?
            self.deltaScangrid2L = [0,0] # to jest przesuniecie lidara [x,y] 1 wzg ukladu wspolrzednych potzebnego do RVIZ, ale nw ktory to xD
            self.deltaScangrid2R = [0,0] # again nw co tu wpisac
            # dla lewego i prawego punktu musi byc to przesuniecie tak, aby punktem odniesienia byl ten sam punkt

            pointcloud = self.ScangridsToPointCloud()
            rospy.loginfo(str(pointcloud))
            #wysylanko
            self.scangridMerged_pub.publish(pointcloud)

        def ScangridsToPointCloud(self):
            fields = [PointField('x', 0, PointField.FLOAT32, 1),
                PointField('y', 4, PointField.FLOAT32, 1)]
            
            header = Header()
            header.frame_id = "frame"
            header.stamp = rospy.Time.now()

            pointsScangrid2L = self.ScangridToXY(self.Scangrid2L,self.deltaScangrid2L[0],self.deltaScangrid2L[1])
            pointsScangrid2R = self.ScangridToXY(self.Scangrid2R,self.deltaScangrid2R[0],self.deltaScangrid2R[1])

            # lista points to punkty pointsScangrid2L, a po nich sa doklejone pointsScangrid2R
            points = np.concatenate((pointsScangrid2L, pointsScangrid2R), axis=0)
            pointcloud = point_cloud2.create_cloud(header, fields, points)
            return pointcloud
        
        def ScangridToXY(self, scangrid, delta_x,delta_y):       
            start_angle = 165                 # index zerowy ma kat 165 stopni wg dokumentacji SICK,a ostani segment ma 15 stopni
            delta_angle = 4.6875              # roznica katow miedzy kolejnymi segmentami

            angle_list = [start_angle - (i*delta_angle) for i in range(33)]  # lista katow, ktore odpowiadaja indeksom
            
            rospy.loginfo("angle_list"+str(angle_list))

            # x i y wzg srodka danego lidara
            x = []
            y = []

            for i,r in enumerate(scangrid):
                y.append(r*math.sin(math.radians(angle_list[i]))+delta_x)
                x.append(r*math.cos(math.radians(angle_list[i]))+delta_y)

            scangrid_xy = np.array([x,y]).reshape(2,-1).T
            rospy.loginfo(scangrid_xy)
            return scangrid_xy

        def Communication(self):
            self.rate.sleep()
            self.ScangridsSender()
            rospy.loginfo('+++++++++<<<<<< COMMUNICATION LOOP >>>>>>++++++++')


if __name__ == '__main__':
    try:    
        rospy.init_node('lidar_to_point_cloud')
        lidar_to_point_cloud = LidarToPointCloud()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')          