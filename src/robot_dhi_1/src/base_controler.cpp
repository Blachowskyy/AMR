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
//#include <geometry_msgs/Pose2D.h>
//#include <tf2/LinearMath/Quaternion.h>
#include <tf/transform_broadcaster.h>
#include <cmath>
//#include "sick_lidar_localization/LocalizationControllerResultMessage0502.h"
 
// Create odometry data publishers
//ros::Publisher odom_data_pub;
//ros::Publisher odom_data_pub_quat;

ros::Publisher comand_curtis_vel_pub;
ros::Publisher comand_servo_angle_pub;
ros::Publisher servo_vel_pub;
ros::Publisher servo_vel_kola_pub;
ros::Publisher servo_Psi_kola_pub;
ros::Publisher V_cel_pub;

ros::Time current_time, last_time;

// nav_msgs::Odometry odomNew;
// nav_msgs::Odometry odomOld;
// nav_msgs::Odometry sickOdom;
nav_msgs::Odometry Odom;
//geometry_msgs::Pose2D odomPose2D;
std_msgs::Int64 PWM_DutyCycle;
std_msgs::Float32 ServoTick;
std_msgs::Float32 V_wozka;
std_msgs::Float32 V_kola;
std_msgs::Float32 Psi_kola;
std_msgs::Float32 V_cel_msg;

tf::TransformBroadcaster *tb;
 
// Initial pose
//const double initialX = 0.0;
//const double initialY = 0.0;
//const double initialPsi = 0.0;
const double PI = 3.141592;
 
// Robot physical constants
const double TICKS_PER_REVOLUTION = 3215;// For reference purposes.
const double WHEEL_RADIUS = 0.105; 	// Wheel radius in meters
const double BASE = 1.195; 		// Center of turning to direction tire
const double TICKS_PER_METER = 4800; //TICKS_PER_REVOLUTION / (2 * PI * WHEEL_RADIUS);

// Servo physical constants
const double ZERO_SERVO = 0.0;
const double RADIN_MIN = (-42 * PI)/180.0;
const double RADIN_MAX = (42 * PI)/180.0;
const double TICK_MIN = -6 * 7 * 10000 + ZERO_SERVO;
const double TICK_MAX = 6 * 7 * 10000 + ZERO_SERVO;
const double RADIAN_PER_TICKS = ((RADIN_MAX - RADIN_MIN) / ( TICK_MAX - TICK_MIN)); //(10000 * 180)/(7 * PI); 
  
// distance_Rob both wheels have traveled
double DeltaDistanceKolo = 0.0;
double DeltaDistanceKolo_1 = 0.0;
//double twistServo = 0.0;
double Psi = 0.0;
double V = 0;
float Vw = 0;
double Fi = 0;
double Fi_dot = 0;
long int KoloLastCount = 0;
//long int ServoLastCount = 0;
double controlWozekPWM  = 0;
double controlKoloAngle  = 0;
double V_zad = 0;
double V_cel = 0;
double X_dot1 = 0;
double Y_dot1 = 0;
double Fi_dot_zad = 0;
double Fi_dot1 = 0;
//double TimeOld = 0;
double d_t = 0;
int Move = 0;
int iii = 0;
double tt = 0;
double Dist_mm = 0;
float Vw1 = 0;

 
// Flag to see if initial pose has been received
//bool initialPoseRecieved = false;
 
using namespace std;
  
// Calculate the distance_Rob the wheel has traveled since the last cycle
// void DistanceCalc(const std_msgs::Int64& Count) {
              
//     if(Move==0) {
//       KoloLastCount = Count.data;
//       Move=1;
//       }
//     else {
// 	    Dist_mm = (Count.data - KoloLastCount);
//       if (abs(Dist_mm )< 65000) {
//         current_time = ros::Time::now();
//         d_t = (current_time - last_time).toSec(); 
//         //Dist_mm  = DeltaDistanceKolo * 10000.0;
//         DeltaDistanceKolo = (double)Dist_mm /10000.0;
//         Vw =  DeltaDistanceKolo / d_t;
//         //Data filtration
//         //float alfa = 0.98;
//         //DeltaDistanceKolo = alfa * DeltaDistanceKolo + (1 - alfa) * DeltaDistanceKolo_1;
        
//         KoloLastCount = Count.data;
//         last_time = current_time;
//         }
//       else {}    
      
//     //ROS_INFO_STREAM("DistanceCalc Ticks Count.data = "<<Count.data<<"  DeltaDistanceKolo  = "<<DeltaDistanceKolo);
  
//     }
// }

//funkcja uwzglednia fakt przechodzenia przez '0'
void DistanceCalc(const std_msgs::Float32& Count) {
  ROS_INFO_STREAM("DistanceCalc");
  //zalozenie, ze w czasie 1 iteracji kolo nie moze zrobic wiecej tikow niz polowa tikow
  // int max_ticks_iter = 2000;
  // int KoloCount = Count.data;
  // DeltaDistanceKolo = (KoloCount - KoloLastCount);
  // KoloLastCount = KoloCount;

  //   //przypadki przekroczenia punktu '0'
  //   if (abs(DeltaDistanceKolo) > max_ticks_iter)     {
  //     //ticks = -(TICKS_PER_REVOLUTION - ticks);
  //   }
  //   else  {
  //   current_time = ros::Time::now();
  //   DeltaDistanceKolo = DeltaDistanceKolo / 1000;
  //   d_t = (current_time - last_time).toSec();

    // Vw1 = DeltaDistanceKolo/d_t; // w m/s
    double WozekVw = Count.data;
    float alfa = 0.0;
    // Vw = alfa * Vw + (1 - alfa) * WozekVw;
    Vw = WozekVw;
    // last_time = current_time;
    //Psi = (controlKoloAngle * PI)/ 180.0;

    // }
  ROS_INFO_STREAM("Wozek_speed = "<<Count.data);
  //ROS_INFO_STREAM(" d_t="<<d_t<< " vw1 " <<Vw1<< "VW= " <<Vw);
}




void AngleCalc(const std_msgs::Float32& Count) {

  //long int angleTics = Count.data - ServoLastCount;
  //twistSerwo = double(TICKS_PER_RADIAN * angleTics);
  //Psi = ( (double)Count.data/TICKS_PER_RADIAN);
  Psi = (PI / 180) * (double)Count.data;
  ROS_INFO_STREAM("AngleCalc Psi Count.data = "<<Count.data<<" Psi = "<<Psi);
  //ServoLastCount = Count.data;
} 

 void OdomData(const nav_msgs::Odometry OdomGet)  {
   //ROS_INFO("OdomData");
   X_dot1 = (double)OdomGet.twist.twist.linear.x;
   Y_dot1 = (double)OdomGet.twist.twist.linear.y;
   Fi_dot1 = (double)OdomGet.twist.twist.angular.z;
   
	
  	tf::Quaternion q(
        OdomGet.pose.pose.orientation.x,
        OdomGet.pose.pose.orientation.y,
        OdomGet.pose.pose.orientation.z,
        OdomGet.pose.pose.orientation.w);
   tf::Matrix3x3 m(q);
   double roll, pitch, yaw;
   m.getRPY(roll, pitch, yaw);
   Fi = yaw;
   Fi_dot = Fi_dot1;
   V = cos(Fi) * X_dot1 + sin(Fi) * Y_dot1;
   V_cel = V;
   
  	// Calculate the wozek velocity in meters per secound 
  //V = Vw * cos(Psi);
  	// Calculate the twist velocity radians per secound
  //Fi_dot = Vw * (sin(Psi)/BASE);  
   
   //V = sqrt( pow(X_dot1, 2) + pow(Y_dot1, 2) );
   //double PSI1 = (double)Odom.pose.pose.orientation.z;
   //Odom = OdomGet;
 //ROS_INFO_STREAM("Odom X_dot ="<<X_dot1<<" Y_dot="<<Y_dot1<<" V ="<<V<<" Fi_dot="<<Fi_dot);
 }

 void VelDest(const geometry_msgs::Twist& cmdVel) {
  double V_zad_1 = (double)cmdVel.linear.x;
  double Fi_dot_zad_1 = (double)cmdVel.angular.z;

  float alfa = 0.0;
  V_zad = alfa * V_zad + (1 - alfa) * V_zad_1;
  Fi_dot_zad = alfa * Fi_dot_zad + (1 - alfa) * Fi_dot_zad_1;
  
   //V = sqrt( pow(X_dot1, 2) + pow(Y_dot1, 2));
    
   

  //ROS_INFO_STREAM("VelDest V_zad ="<<V_zad<<" Fi_dot_zad="<<Fi_dot_zad);
  //ROS_INFO_STREAM("VelDest Psi = "<<Psi<<" Vw= "<< Vw <<" V= "<<V<<" Fi_dot =" <<Fi_dot);
 }

// Take the velocity command as input and calculate the PWM values.
void BaseControler()  {         //const geometry_msgs::Twist& cmdVel) {
          
   ROS_INFO("BaseControler");
   
  
   double Delta_V = (V_zad - V);
   double regulator = 0;
   if (abs(V_zad) != 0.0){
      regulator = 1000; 
      }
   else {
      regulator = 1500;           //???????????????????????
   }
  
   controlWozekPWM = controlWozekPWM + (regulator * Delta_V);
  // controlWozekPWM = 3000;

   if ((controlWozekPWM > -1200) && (controlWozekPWM < 1200)){
    controlWozekPWM = controlWozekPWM;
    //controlWozekPWM = controlWozekPWM + ((300.0 ) * Delta_V);
    //controlWozekPWM = 3000*sin(2*PI*0.1*0.1*tt);
     }   
  else{
   if (controlWozekPWM>=1200){
        controlWozekPWM=1199;
        }
      else if (controlWozekPWM<=-1200){
        controlWozekPWM= -1199;
        }
  }
   ROS_INFO_STREAM("BaseControler V_zad ="<<V_zad<<" V="<<V<<" Delta_V="<<Delta_V<<" controlWozekPWM ="<<controlWozekPWM);
 
  // Calculate the Servo position value given the desired angle 

  // double Delta_Fi_dot = (Fi_dot_zad - Fi_dot);
  // // controlKoloAngle = 0;
  // if (controlWozekPWM > 0) {
  //   controlKoloAngle = (controlKoloAngle  + 12.0* (180.0 / PI) * Delta_Fi_dot);
  // }
  // else if(controlWozekPWM < 0)  {
  //   controlKoloAngle = (controlKoloAngle  + 12.0 * (180.0 / PI) * (-1) * Delta_Fi_dot);
  // }
  // else {
  //   controlKoloAngle = controlKoloAngle;
  // }

if (Vw!= 0) {
  double arg = (Fi_dot_zad * BASE)/ Vw ;
  if (arg > 1) {
    arg = 1;
  }
  else if (arg < -1)  {
    arg = -1;
  }
  else{
    arg = arg;
  }

  controlKoloAngle = (180.0 / PI) * asin(arg);
  //double Delta_Fi_dot = (Fi_dot_zad - ((Vw * sin(arg))/BASE));
  //controlKoloAngle = controlKoloAngle + (1 * (180.0 / PI)* Delta_Fi_dot);

  }
else  {
  controlKoloAngle = 0;
}
  
  if ((controlKoloAngle <= 90) && (controlKoloAngle >= -90))  {
    
    controlKoloAngle = controlKoloAngle;
    
  }
  else  {
    if (controlKoloAngle > 90)  {  
      controlKoloAngle = 90;
      }
    else  if (controlKoloAngle < -90)  {  
      controlKoloAngle = -90;
      }
  }
  
  // ROS_INFO_STREAM("BaseControler Fi_dot_zad ="<<Fi_dot_zad<<" Fi_dot="<<Fi_dot<<" Delta_Fi_dot="<<Delta_Fi_dot<<" controlKoloAngle ="<<controlKoloAngle);
   
}



int main(int argc, char **argv) {
 
 // Launch ROS and create a node
  ros::init(argc, argv, "base_controler");
  ros::NodeHandle node; 

  current_time = ros::Time::now();
  last_time = ros::Time::now();  

  // Subscribe to ROS topics
  // ros::Subscriber subForTickCounts = node.subscribe("wozek_speed", 1, DistanceCalc,  ros::TransportHints().tcpNoDelay());
  ros::Subscriber subForTickCounts = node.subscribe("Forklift/drive/actual_speed", 1, DistanceCalc,  ros::TransportHints().tcpNoDelay());
  // ros::Subscriber subForAngeCounts = node.subscribe("servo_angle_tick", 1, AngleCalc, ros::TransportHints().tcpNoDelay());
  ros::Subscriber subForAngeCounts = node.subscribe("Forklift/drive/current_servo_angle", 1, AngleCalc, ros::TransportHints().tcpNoDelay());
  ros::Subscriber subCmdVel = node.subscribe("cmd_vel", 1, VelDest, ros::TransportHints().tcpNoDelay());
  ros::Subscriber subOdom = node.subscribe("odom", 1, OdomData, ros::TransportHints().tcpNoDelay());
   
  //odom_data_pub = node.advertise<nav_msgs::Odometry>("odom", 30);
  // comand_curtis_vel_pub = node.advertise<std_msgs::Int64>("comand_curtis_vel", 1);
  // comand_servo_angle_pub = node.advertise<std_msgs::Float32>("comand_servo_angle", 1);  
  comand_curtis_vel_pub = node.advertise<std_msgs::Int64>("Forklift/control/PWM_curtis", 1);
  comand_servo_angle_pub = node.advertise<std_msgs::Float32>("Forklift/control/servo_angle", 1);
  servo_vel_pub = node.advertise<std_msgs::Float32>("servo_vel", 1);
  servo_vel_kola_pub = node.advertise<std_msgs::Float32>("servo_vel_kola", 1);
  servo_Psi_kola_pub = node.advertise<std_msgs::Float32>("servo_Psi_kola", 1);
  V_cel_pub = node.advertise<std_msgs::Float32>("V_cel", 1);



  //ros::Time::init();
  ros::Rate loop_rate(10); 
     
  while(ros::ok()) {
      
   // if(initialPoseRecieved) {
    ROS_INFO("LOOP CONTROLER");
      //update_odom();
      //publish_quat();
      //update_trans();
      //UpdateOdom();
      BaseControler();
      PWM_DutyCycle.data = controlWozekPWM;
      comand_curtis_vel_pub.publish((std_msgs::Int64)PWM_DutyCycle);
      ServoTick.data  = controlKoloAngle;
      comand_servo_angle_pub.publish((std_msgs::Float32)ServoTick);
      V_wozka.data = V;
      servo_vel_pub.publish((std_msgs::Float32)V_wozka);      
      V_kola.data = Vw;
      servo_vel_kola_pub.publish((std_msgs::Float32)V_kola); 
      Psi_kola.data = Psi;
      servo_Psi_kola_pub.publish((std_msgs::Float32)Psi_kola); 
      V_cel_msg.data = V_cel;
      V_cel_pub.publish((std_msgs::Float32)V_cel_msg); 

   // }
    ros::spinOnce();
    loop_rate.sleep();
  }
 
  return 0;
}

