#!/usr/bin/env python

import math
from math import sin, cos, pi

import rospy
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Pose, Quaternion, Twist, Vector3

rospy.init_node('fejk_odometry_publisher')
rospy.loginfo("start fejk odom")

pub = rospy.Publisher("fejkodom", Odometry, queue_size=10)
rate = rospy.Rate(2)

current_time = rospy.Time.now()
last_time = rospy.Time.now()


while not rospy.is_shutdown():

    current_time = rospy.Time.now()

    # compute odometry in a typical way given the velocities of the robot
    dt = (current_time - last_time).to_sec()
    x = 0
    y = 0
    th = 0


    odom = Odometry()
    odom.header.stamp = current_time
    odom.header.frame_id = "fejkodom"

    # set the position
    odom.pose.pose = Pose(Point(x, y, 0.), Quaternion(0,0,0,0))

    # set the velocity
    odom.child_frame_id = "base_link"
    odom.twist.twist = Twist(Vector3(0, 0, 0), Vector3(0, 0, 0))
    
    pub.publish(odom)

    rate.sleep()

