/*
 * Subscribe: This node will subscribe to the following topics:
 * /servo_angle_tick: Angle of direction wheel (std_msgs/Int64)
 * 
 *  /wozek_angle_tick : Tick counts from the  motor encoder  (std_msgs/Int64)
 * 
 *  /cmd_vel
 *
 *  /initial_2d : The initial position and orientation of the robot.
 *               (geometry_msgs/PoseStamped)
 *
 * Publish: This node will publish to the following topics:
 *  odom_data_euler : Position and velocity estimate. The orientation.z 
 *                    variable is an Euler angle representing the yaw angle.
 *                    (nav_msgs/Odometry)
 *  odom_data_quat : Position and velocity estimate. The orientation is 
 *                   in quaternion format.
 *                   (nav_msgs/Odometry)
 */
 
// Include various libraries
#include "ros/ros.h"
#include <string>
#include "std_msgs/Int64.h"
#include "std_msgs/Float32.h"
#include <nav_msgs/Odometry.h>
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/TransformStamped.h>
//#include <tf2/LinearMath/Quaternion.h>
#include <tf/transform_broadcaster.h>
#include <cmath>
#include "sick_lidar_localization/LocalizationControllerResultMessage0502.h"
 
// Create odometry data publishers
ros::Publisher odom_data_pub;
ros::Publisher odom_data_pub_quat;

ros::Publisher comand_curtis_vel_pub;
ros::Publisher comand_servo_angle_pub;
nav_msgs::Odometry odomNew;
nav_msgs::Odometry odomOld;
nav_msgs::Odometry sickOdom;
std_msgs::Int64 PWM_DutyCycle;
std_msgs::Int64 ServoTick;

tf::TransformBroadcaster *tb;
 
// Initial pose
const double initialX = 0.0;
const double initialY = 0.0;
const double initialPsi = 0.0;
const double PI = 3.141592;
 
// Robot physical constants
const double TICKS_PER_REVOLUTION = 3215;// For reference purposes.
const double WHEEL_RADIUS = 0.105; 	// Wheel radius in meters
const double BASE = 1.195; 		// Center of turning to direction tire
const double TICKS_PER_METER = 4800; //TICKS_PER_REVOLUTION / (2 * PI * WHEEL_RADIUS);

// Servo physical constants
const double ZERO_SERVO = 55207.0;
const double RADIN_MIN = (-42 * PI)/180.0;
const double RADIN_MAX = (42 * PI)/180.0;
const double TICK_MIN = -6 * 7 * 10000 + ZERO_SERVO;
const double TICK_MAX = 6 * 7 * 10000 + ZERO_SERVO;
const double RADIAN_PER_TICKS = ((RADIN_MAX - RADIN_MIN) / ( TICK_MAX - TICK_MIN)); //(10000 * 180)/(7 * PI); 
  
// distance_Rob both wheels have traveled
double DeltaDistanceKolo = 0.0;
//double twistServo = 0.0;
double Psi = 0.0;
long int KoloLastCount = 0;
//long int ServoLastCount = 0;
double controlWozekPWM  = 0;
double controlKoloAngle  = 0;
 
// Flag to see if initial pose has been received
bool initialPoseRecieved = false;
 
using namespace std;
 
// Get initial_2d message from either Rviz clicks or a manual pose publisher
void set_initial_2d(const geometry_msgs::PoseStamped &rvizClick) {
 
  odomOld.pose.pose.position.x = rvizClick.pose.position.x;
  odomOld.pose.pose.position.y = rvizClick.pose.position.y;
  odomOld.pose.pose.orientation.z = rvizClick.pose.orientation.z;
  initialPoseRecieved = true;
}


 void update_trans() {

  ROS_INFO("update transform");

 // transform message declarations
  tb = new tf::TransformBroadcaster();
  geometry_msgs::TransformStamped transformStamped;
  transformStamped.header.frame_id = "odom";
  transformStamped.child_frame_id = "base_footprint";
  
  
//   // update transform
 	transformStamped.header.stamp = ros::Time::now(); 
 	transformStamped.transform.translation.x = sickOdom.pose.pose.position.x; 
 	transformStamped.transform.translation.y = sickOdom.pose.pose.position.y; 
 	transformStamped.transform.translation.z = 0.0;
 	transformStamped.transform.rotation = tf::createQuaternionMsgFromYaw(sickOdom.pose.pose.orientation.z);

 	tb->sendTransform(transformStamped);	
 }
 
// Calculate the distance_Rob the wheel has traveled since the last cycle
void DistanceCalc(const std_msgs::Int64& Count) {
          
    long int Ticks = (Count.data - KoloLastCount);
    DeltaDistanceKolo = (double)Ticks/TICKS_PER_METER;
    KoloLastCount = Count.data;
    ROS_INFO_STREAM("DistanceCalc Ticks Count.data = "<<Count.data<<"  DeltaDistanceKolo = "<<DeltaDistanceKolo);
}

void AngleCalc(const std_msgs::Int64& Count) {

  //long int angleTics = Count.data - ServoLastCount;
  //twistSerwo = double(TICKS_PER_RADIAN * angleTics);
  //Psi = ( (double)Count.data/TICKS_PER_RADIAN);
  Psi = (RADIAN_PER_TICKS * ((double)Count.data - ZERO_SERVO));
  ROS_INFO_STREAM("AngleCalc Psi Count.data = "<<Count.data<<" Psi = "<<Psi);
  //ServoLastCount = Count.data;
}

// Take the velocity command as input and calculate the PWM values.
void BaseControler(const geometry_msgs::Twist& cmdVel) {
          
   double alfa = 0.8;
   double V_zad = (double)cmdVel.linear.x;
   double Fi_dot_zad = (double)cmdVel.angular.z;
   double V = (double)odomNew.twist.twist.linear.x;
   double Fi_dot = (double)odomNew.twist.twist.angular.z;
   
   ROS_INFO("BaseControler");
   // Data filtration
   V = alfa * V + (1 - alfa) * (double)odomOld.twist.twist.linear.x;
   Fi_dot = alfa * Fi_dot + (1 - alfa) * (double)odomOld.twist.twist.angular.z;
   
   // Calculate the PWM value given the desired velocity 
   double Delta_V = V_zad- V;
   controlWozekPWM = controlWozekPWM + ((100000/TICKS_PER_METER) * Delta_V);
   //ROS_INFO_STREAM("V_zad ="<<V_zad<<" V="<<V<<" Delta_V="<<Delta_V<<" controlWozekPWM ="<<controlWozekPWM);
 
     // Calculate the Servo position value given the desired angle 
  double Delta_Fi_dot = Fi_dot_zad- Fi_dot;
  //controlKoloAngle = controlKoloAngle+ (100 * Delta_Fi_dot);
  controlKoloAngle = (1000 * Delta_Fi_dot);
  //ROS_INFO_STREAM("Fi_dot_zad ="<<Fi_dot_zad<<" Fi_dot="<<Fi_dot<<" Delta_Fi_dot="<<Delta_Fi_dot<<" controlKoloAngle ="<<controlKoloAngle);
   
}

// Take angle from LidarLoc
void LidarLocPose(const sick_lidar_localization::LocalizationControllerResultMessage0502 &msg) {
    double x = msg.x/1000.0;
    double y = msg.y/1000.0;
    double yaw = ((msg.heading/1000.0) * PI)/180.0;

    sickOdom.pose.pose.position.x = x;
    sickOdom.pose.pose.position.y = y;
    sickOdom.pose.pose.orientation.z = yaw;


    //ROS_INFO_STREAM("x= "<< x <<" y= "<< y <<" yaw= "<<yaw);
    //ROS_INFO_STREAM("nav x= "<< sickOdom.pose.pose.position.x <<" nav y= "<< sickOdom.pose.pose.position.y <<" nav yaw= "<<sickOdom.pose.pose.orientation.z);
}

// Publish a nav_msgs::Odometry message in quaternion format
void publish_quat() {

  ROS_INFO("publish quat");
 
  tf2::Quaternion q;
  q.setRPY(0, 0, odomNew.pose.pose.orientation.z);
 
  nav_msgs::Odometry quatOdom;
  quatOdom.header.stamp = odomNew.header.stamp;
  quatOdom.header.frame_id = "odom";
  quatOdom.child_frame_id = "base_link";
  quatOdom.pose.pose.position.x = odomNew.pose.pose.position.x;
  quatOdom.pose.pose.position.y = odomNew.pose.pose.position.y;
  quatOdom.pose.pose.position.z = odomNew.pose.pose.position.z;
  quatOdom.pose.pose.orientation.x = q.x();
  quatOdom.pose.pose.orientation.y = q.y();
  quatOdom.pose.pose.orientation.z = q.z();
  quatOdom.pose.pose.orientation.w = q.w();
  quatOdom.twist.twist.linear.x = odomNew.twist.twist.linear.x;
  quatOdom.twist.twist.linear.y = odomNew.twist.twist.linear.y;
  quatOdom.twist.twist.linear.z = odomNew.twist.twist.linear.z;
  quatOdom.twist.twist.angular.x = odomNew.twist.twist.angular.x;
  quatOdom.twist.twist.angular.y = odomNew.twist.twist.angular.y;
  quatOdom.twist.twist.angular.z = odomNew.twist.twist.angular.z;
 
  for(int i = 0; i<36; i++) {
    if(i == 0 || i == 7 || i == 14) {
      quatOdom.pose.covariance[i] = .01;
     }
     else if (i == 21 || i == 28 || i== 35) {
       quatOdom.pose.covariance[i] += 0.1;
     }
     else {
       quatOdom.pose.covariance[i] = 0;
     }
  }
 odom_data_pub_quat.publish(quatOdom);
}
 
// // Update odometry information
// void update_odom() {

//   ROS_INFO("update_odom");
//   odomNew.header.stamp = ros::Time::now();
//   // Calculate the time step
//   double DeltaTime = (odomNew.header.stamp.toSec() - odomOld.header.stamp.toSec());
//   // Calculate the wheel velocity in meters per secound 
//   double Vw = DeltaDistanceKolo/DeltaTime;
//     // Calculate the wozek velocity in meters per secound 
//   double V = Vw * cos(Psi);
//   // Calculate the twist velocity radians per secound
//   double Fi_dot = V * (sin(Psi)/BASE);
//   double Fi = odomOld.pose.pose.orientation.z;

//   ROS_INFO_STREAM("DeltaTime = "<<DeltaTime);

//   // Calculate the velocity 
//   double X_dot = V * cos(Fi);
//   double Y_dot = V * sin(Fi);
//          Fi_dot = Fi_dot;
//   ROS_INFO_STREAM("Psi = "<<Psi<<" Vw= "<<Vw<<" V= "<<V<<" Fi =" <<Fi);

// /*
//   // Calculate the position 
//   double X += X_dot * DeltaTime;
//   double Y += Y_dot * DeltaTime;
//   double Fi += Fi_dot * DeltaTime;


//   // Average angle during the last cycle
//   double avgAngle = cycleAngle;
     
//   if (avgAngle > PI) {
//     avgAngle -= 2*PI;
//   }
//   else if (avgAngle < -PI) {
//     avgAngle += 2*PI;
//   }
//   else{}
//   */
 
//   // Calculate the new pose (x, y, and theta)
//   odomNew.pose.pose.position.x = odomOld.pose.pose.position.x + X_dot * DeltaTime;
//   odomNew.pose.pose.position.y = odomOld.pose.pose.position.y + Y_dot * DeltaTime;
//   odomNew.pose.pose.orientation.z = odomOld.pose.pose.orientation.z + Fi_dot * DeltaTime;
 
//   // Prevent lockup from a single bad cycle
//   if (isnan(odomNew.pose.pose.position.x) || isnan(odomNew.pose.pose.position.y)
//      || isnan(odomNew.pose.pose.position.z)) {
//     odomNew.pose.pose.position.x = odomOld.pose.pose.position.x;
//     odomNew.pose.pose.position.y = odomOld.pose.pose.position.y;
//     odomNew.pose.pose.orientation.z = odomOld.pose.pose.orientation.z;
//   }
 
//   // Make sure theta stays in the correct range
//   if (odomNew.pose.pose.orientation.z > PI) {
//     odomNew.pose.pose.orientation.z -= 2 * PI;
//   }
//   else if (odomNew.pose.pose.orientation.z < -PI) {
//     odomNew.pose.pose.orientation.z += 2 * PI;
//   }
//   else{}
  
 
//   // Compute the velocity
//   //odomNew.header.stamp = ros::Time::now();
//   odomNew.twist.twist.linear.x = V;  //cycledistance_Rob/(odomNew.header.stamp.toSec() - odomOld.header.stamp.toSec());
//   odomNew.twist.twist.angular.z = Fi_dot;  //cycleAngle/(odomNew.header.stamp.toSec() - odomOld.header.stamp.toSec());
//   ROS_INFO_STREAM("V = odomNew.twist.twist.linear.x ="<<odomNew.twist.twist.linear.x);
//   ROS_INFO_STREAM("Fi_dot = odomNew.twist.twist.angular.z ="<<odomNew.twist.twist.angular.z);

 
//   // Save the pose data for the next cycle
//   odomOld.pose.pose.position.x = odomNew.pose.pose.position.x;
//   odomOld.pose.pose.position.y = odomNew.pose.pose.position.y;
//   odomOld.pose.pose.orientation.z = odomNew.pose.pose.orientation.z;
//   odomOld.header.stamp = odomNew.header.stamp;
  
//   // Publish the odometry message
//   odom_data_pub.publish(odomNew);

// }

// Update odometry information
void update_odom() {

  ROS_INFO("update_odom");

  odomNew = sickOdom;
  odomNew.header.stamp = ros::Time::now();
  odomNew.header.frame_id = "odom";
  odomNew.child_frame_id = "base_link";
  
  // Publish the odometry message
  odom_data_pub.publish(odomNew);

}



int main(int argc, char **argv) {
 
 // Launch ROS and create a node
  ros::init(argc, argv, "odom_pub");
  ros::NodeHandle node;  


  // Set the data fields of the odometry message
  odomNew.header.frame_id = "odom";
  odomNew.header.stamp = ros::Time::now();;
  odomNew.child_frame_id = "base_footprint";

  odomNew.pose.pose.position.z = 0;
  odomNew.pose.pose.orientation.x = 0;
  odomNew.pose.pose.orientation.y = 0;
  odomNew.twist.twist.linear.x = 0;
  odomNew.twist.twist.linear.y = 0;
  odomNew.twist.twist.linear.z = 0;
  odomNew.twist.twist.angular.x = 0;
  odomNew.twist.twist.angular.y = 0;
  odomNew.twist.twist.angular.z = 0;
  odomOld.pose.pose.position.x = initialX;
  odomOld.pose.pose.position.y = initialY;
  odomOld.pose.pose.orientation.z = initialPsi;
  
   
  // Subscribe to ROS topics
  ros::Subscriber subForTickCounts = node.subscribe("wozek_angle_tick", 30, DistanceCalc,  ros::TransportHints().tcpNoDelay());
  ros::Subscriber subForAngeCounts = node.subscribe("servo_angle_tick", 30, AngleCalc, ros::TransportHints().tcpNoDelay());
  ros::Subscriber subCmdVel = node.subscribe("cmd_vel", 30, BaseControler, ros::TransportHints().tcpNoDelay());
  
  ros::Subscriber subInitialPose = node.subscribe("initial_2d", 1, set_initial_2d);
  ros::Subscriber subLidarLocPose = node.subscribe("localizationcontroller/out/localizationcontroller_result_message_0502", 30, LidarLocPose);
 
  // Publisher of simple odom message where orientation.z is an euler angle
  odom_data_pub = node.advertise<nav_msgs::Odometry>("odom", 30);
 
  // Publisher of full odom message where orientation is quaternion
  odom_data_pub_quat = node.advertise<nav_msgs::Odometry>("odom_data_quat", 30);
  
  
  // Publisher of simple odom message where orientation.z is an euler angle
  comand_curtis_vel_pub = node.advertise<std_msgs::Int64>("comand_curtis_vel", 30);
  comand_servo_angle_pub = node.advertise<std_msgs::Int64>("comand_servo_angle", 30);
  
 

  //ros::Time::init();
  ros::Rate loop_rate(100); 
     
  while(ros::ok()) {
      
   // if(initialPoseRecieved) {
    ROS_INFO("LOOP");
      update_odom();
      publish_quat();
      update_trans();
      
      PWM_DutyCycle.data = controlWozekPWM;
      comand_curtis_vel_pub.publish((std_msgs::Int64)PWM_DutyCycle);
      ServoTick.data  = controlKoloAngle;
      comand_servo_angle_pub.publish((std_msgs::Int64)ServoTick);
      
   // }
    ros::spinOnce();
    loop_rate.sleep();
  }
 
  return 0;
}

