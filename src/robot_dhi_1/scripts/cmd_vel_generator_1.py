#!/usr/bin/env python3


import rospy
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion
from geometry_msgs.msg import Point, Twist
from math import atan2

x = 0.0
y = 0.0 
theta = 0.0
Vx = 0.0
Vy = 0.0
Vtheta = 0.0

def newOdom(msg):
    global x
    global y
    global theta
    global Vx
    global Vy
    global Vtheta

    x = msg.pose.pose.position.x
    y = msg.pose.pose.position.y

    rot_q = msg.pose.pose.orientation
    (roll, pitch, theta) = euler_from_quaternion([rot_q.x, rot_q.y, rot_q.z, rot_q.w])
    
    Vx = msg.twist.twist.linear.x
    Vy = msg.twist.twist.linear.y
    Vtheta = msg.twist.twist.angular.z

rospy.init_node("speed_controller")

sub = rospy.Subscriber("odom", Odometry, newOdom)
pub = rospy.Publisher("cmd_vel", Twist, queue_size = 1)

speed = Twist()

r = rospy.Rate(1)

goal = Point()
goal.x = 5
goal.y = 5

while not rospy.is_shutdown():
#    inc_x = goal.x -x
#    inc_y = goal.y -y
#
#    angle_to_goal = atan2(inc_y, inc_x)
#
#    if abs(angle_to_goal - theta) > 0.1:
#        speed.linear.x = 0.0
#        speed.angular.z = 0.3
#    else:
#        speed.linear.x = 0.5
#        speed.angular.z = 0.0
	if rospy.has_param('/speed/X'):
		vel_lin = float(rospy.get_param("/speed/X"))
		rospy.loginfo(f'/speed_x= {vel_lin} ' )
		speed.linear.x = vel_lin
	else:
		speed.linear.x = 0.0
		
	if rospy.has_param('/speed/Fi'):
		vel_ang = float(rospy.get_param("/speed/Fi"))
		rospy.loginfo(f'/speed_Fi= {vel_ang} ' )
		speed.angular.z = vel_ang
	else:
		speed.angular.z = 0.0
	
	rospy.loginfo(f'cmd_vel X_dot = {speed.linear.x} cmd_vel Fi_dot = {speed.angular.z}' )		
	rospy.loginfo(f'Odom X = {x:.3f} Y = {y:.3f} Fi = {theta:.3f}' )
	rospy.loginfo(f'Odom Vx = {Vx:.3f} Vy = {Vy:.3f} Fi_dot = {Vtheta:.3f}' )

	pub.publish(speed)
	r.sleep() 