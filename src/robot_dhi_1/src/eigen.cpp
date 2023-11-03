
#include "ros/ros.h"
#include "std_msgs/String.h"
#include <string>
#include "std_msgs/Int64.h"
#include "std_msgs/Float32.h"
#include <time.h>
#include <iostream>
#include <nav_msgs/Odometry.h>
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/TransformStamped.h>
//#include <tf2/LinearMath/Quaternion.h>

#include <sstream>
#include <eigen3/Eigen/Dense>
//#include <Eigen/Geometry>  
//#include <cmath>
//#include <vector>
//#include <tf.h>

using namespace std;
using std::vector;
using Eigen::MatrixXd;
using Eigen::VectorXd;


// Create odometry data publishers
ros::Publisher odom_data_pub;
//ros::Publisher odom_data_pub_quat;
/*ros::Publisher Lidar_x_pub;
ros::Publisher Lidar_y_pub;
ros::Publisher Lidar_Fi_pub;

ros::Publisher Wozek_Vw_pub;
ros::Publisher Wozek_Psi_pub;

ros::Publisher x1_pub;
ros::Publisher x2_pub;
ros::Publisher x3_pub;*/

//ros::Publisher comand_curtis_vel_pub;
//ros::Publisher comand_servo_angle_pub;
nav_msgs::Odometry odomNew;
//nav_msgs::Odometry odomOld;
nav_msgs::Odometry sickOdom;
//std_msgs::Int64 PWM_DutyCycle;
//std_msgs::Int64 ServoTick;
/*std_msgs::Float32 Lidar_x_msgs;
std_msgs::Float32 Lidar_y_msgs;
std_msgs::Float32 Lidar_Fi_msgs;*/

/*std_msgs::Float32 Wozek_Vw_msgs;
std_msgs::Float32 Wozek_Psi_msgs;*/

/*std_msgs::Float32 x1_msgs;
std_msgs::Float32 x2_msgs;
std_msgs::Float32 x3_msgs;*/

double DeltaTime = 0, TimeOld = 0, Czas=0;
double Vw=0, V=0, Psi = 0, Fi_dot=0, Fi=0, Lidar_x=0, Lidar_y=0, Lidar_Fi=0;
double x=0, y=0, fi=0, Wozek_Vw=0, Wozek_Psi=0;
double d_t=0.0;
double Angle = 0;
double BASE = 1.195; 
double PI = 3.141592;
long time_i = 0;
int ii = 1;
 
  
  
Eigen::Matrix3d A;

Eigen::Matrix3d A_T;

Eigen::MatrixXd B_k_1(3, 2);			

//Measurement matrix H_k
Eigen::Matrix3d H;

Eigen::Matrix3d H_T; 		

	
//Sensor measurement noise covariance matrix R_k
 Eigen::Matrix3d R_k;
 
// State model noise covariance matrix Q_k
Eigen::Matrix3d Q_k;

Eigen::Matrix3d K_k;

Eigen::Matrix3d S_k;

Eigen::Matrix3d invS_k;

// State covariance matrix P_k_minus_1
 Eigen::Matrix3d P_k;

Eigen::Vector3d x_k;
Eigen::Vector3d y_k;
Eigen::Vector2d u_k_1;
//Sensor noise vector 
Eigen::Vector3d w_k;
//process_noise
Eigen::Vector3d v_k;  

/*void odom_generator()		{

ROS_INFO("odom_generator");
    // Calculate the  velocity in meters per secound 
   Czas = Czas + DeltaTime;

  	Vw = 1.5 * sin(2 * PI* 0.01 * Czas ) + 1.5;
  	Psi = (PI/180) * 40 * sin(2 * PI* 0.001* Czas );
  	
  	// random generation between either 0 or 1:
   srand(time(NULL));
   double w_i1 = (((rand() % 1000)/ 1000.0) - 0.5)/100.0;
   srand(time(NULL));
   double w_i2 = (((rand() % 1000)/1000.0) - 0.5)/100.0;
  	
   	Lidar_x = Lidar_x + Vw *cos(Psi) * DeltaTime + w_i1;
   	Lidar_y = Lidar_y + Vw *sin(Psi) * DeltaTime + w_i1;
   	Lidar_Fi = Lidar_Fi + Vw *sin(Psi)/BASE * DeltaTime + w_i2;
   	
  ROS_INFO_STREAM("Czas = "<<Czas);
  /*ROS_INFO_STREAM("DeltaTime = "<<DeltaTime);
  ROS_INFO_STREAM("Vw  = "<< Vw  << "  Psi  ="<< Psi);
  ROS_INFO_STREAM("Lidar_x = "<< Lidar_x << "  Lidar_y ="<< Lidar_y<< "  Lidar_Fi ="<< Lidar_Fi);
  ROS_INFO_STREAM("w_i1 = "<< w_i1 << "  w_i2  ="<< w_i2);
    
   srand(time(NULL));
  	w_i1 = (((rand() % 1000)/ 1000.0) - 0.5)/100.0;
   srand(time(NULL));
   w_i2 = (((rand() % 1000)/ 1000.0) - 0.5)/100.0;
   
   	Wozek_Vw = Vw + w_i1;
   	Wozek_Psi = Psi + w_i2;
    
 ROS_INFO_STREAM("Wozek_Vw  = "<< Wozek_Vw  << "  Wozek_Psi  ="<< Wozek_Psi);
 ROS_INFO_STREAM("w_i1 = "<< w_i1 << "  w_i2  ="<< w_i2);
}  */

void GetWozek_Vw(const std_msgs::Float32& Count) {
          
    Wozek_Vw = Count.data;
    
    ROS_INFO_STREAM("Wozek_Vw  = "<<Wozek_Vw);
}

void GetWozek_Psi(const std_msgs::Float32& Count) {
          
    Wozek_Psi = Count.data;
    
    //ROS_INFO_STREAM("Wozek_Psi  = "<<Wozek_Psi);
}


// Take angle from LidarLoc
void LidarLocPose( const nav_msgs::Odometry sickOdom) {
    
    Lidar_x = sickOdom.pose.pose.position.x;
    Lidar_y = sickOdom.pose.pose.position.y;
    Lidar_Fi = sickOdom.pose.pose.orientation.z ;


    //ROS_INFO_STREAM("x= "<< x <<" y= "<< y <<" yaw= "<<yaw);
    //ROS_INFO_STREAM("Lidar x= "<< sickOdom.pose.pose.position.x <<" Lidar y= "<< sickOdom.pose.pose.position.y <<" Lidar yaw= "<<sickOdom.pose.pose.orientation.z);
}




// Update odometry information
void update_odom() {
 
   ROS_INFO("update_odom");
   odomNew.header.stamp = ros::Time::now();
   if (ii == 1)	{
   TimeOld = odomNew.header.stamp.toSec();  
   ii=2; 
   }
   else	{}
   
   
   // Calculate the time step
   DeltaTime = (odomNew.header.stamp.toSec() - TimeOld);
   TimeOld = odomNew.header.stamp.toSec();
   
//odom_generator();  
   
d_t=DeltaTime;

if ((d_t != 0)	&& ((Lidar_x != 0) || (Lidar_x != 0)|| (Lidar_x != 0)))	{
ROS_INFO_STREAM("d_t= "<< d_t );

u_k_1(0,0)	= 	Wozek_Vw * cos(Wozek_Psi);				//V + v_k;
u_k_1(1,0)	= Wozek_Vw * (sin(Wozek_Psi)/BASE);		//Fi_dot + v_k
ROS_INFO_STREAM("u V_dot= "<< u_k_1(0,0)<<" u Fi_dot= "<< u_k_1(1,0) );

y_k	<<	Lidar_x,	Lidar_y,	Lidar_Fi;
ROS_INFO_STREAM("Y x= "<< y_k(0,0)<<" Y y= "<< y_k(1,0) <<" Y yaw= "<<y_k(2,0));
Fi = Fi + (d_t * u_k_1(1,0));

//ROS_INFO_STREAM("Fi = " << Fi);


B_k_1	<<		cos(Fi)*d_t,	0,
         	sin(Fi)*d_t,	0,
         	0,	d_t;
         	
         	
std::cout <<"B_k_1 = "<< B_k_1 << std::endl;
//Predict the state estimate at time k based on the state 

//x_k = A * x_k + B_k_1 * u_k_1 + v_k;
x_k = A * x_k + B_k_1 * u_k_1;
ROS_INFO_STREAM("1 x_k= "<< x_k(0,0)<<" x_k= "<< x_k(1,0) <<" x_k= "<< x_k(2,0) );

//y_k = H * x_k + w_k;


//Calculate the model residual covariance
//A_T = A.transpose();
A_T = A;
P_k =  A * P_k * A_T + Q_k;
//Calculate the measurement residual covariance
//H_T = H.transpose();
H_T = H;
S_k = H * P_k * H_T + R_k;
invS_k = S_k.inverse();

K_k = P_k * H_T * invS_k;

std::cout << K_k << std::endl;

//Estimation
P_k =  P_k - K_k * H * P_k;
x_k = x_k + K_k * (y_k - H * x_k);

ROS_INFO_STREAM("Lidar_x="<< Lidar_x << "  x_k= "<< x_k(0,0)<< " # Lidar_y="<< Lidar_y<< "  y_k="<< x_k(1,0) << " # Lidar_Fi="<< Lidar_Fi << " Fi_k="<< x_k(2,0));
}
else
{}
     
   //double Fi = odomOld.pose.pose.orientation.z;

   //ROS_INFO_STREAM("DeltaTime = "<<DeltaTime);
/*
   // Calculate the velocity 
   double X_dot = V * cos(Fi);
   double Y_dot = V * sin(Fi);
          Fi_dot = Fi_dot;
   ROS_INFO_STREAM("Psi = "<<Psi<<" Vw= "<<Vw<<" V= "<<V<<" Fi =" <<Fi);

 
   // Calculate the position 
   double X += X_dot * DeltaTime;
   double Y += Y_dot * DeltaTime;
   double Fi += Fi_dot * DeltaTime;


   // Average angle during the last cycle
   double avgAngle = cycleAngle;
     
   if (avgAngle > PI) {
     avgAngle -= 2*PI;
   }
   else if (avgAngle < -PI) {
     avgAngle += 2*PI;
   }
   else{}

 
   // Calculate the new pose (x, y, and theta)
   odomNew.pose.pose.position.x = odomOld.pose.pose.position.x + X_dot * DeltaTime;
   odomNew.pose.pose.position.y = odomOld.pose.pose.position.y + Y_dot * DeltaTime;
   odomNew.pose.pose.orientation.z = odomOld.pose.pose.orientation.z + Fi_dot * DeltaTime;
 
   // Prevent lockup from a single bad cycle
   if (isnan(odomNew.pose.pose.position.x) || isnan(odomNew.pose.pose.position.y)
      || isnan(odomNew.pose.pose.position.z)) {
     odomNew.pose.pose.position.x = odomOld.pose.pose.position.x;
     odomNew.pose.pose.position.y = odomOld.pose.pose.position.y;
     odomNew.pose.pose.orientation.z = odomOld.pose.pose.orientation.z;
   }
 
   // Make sure theta stays in the correct range
   if (odomNew.pose.pose.orientation.z > PI) {
     odomNew.pose.pose.orientation.z -= 2 * PI;
   }
   else if (odomNew.pose.pose.orientation.z < -PI) {
     odomNew.pose.pose.orientation.z += 2 * PI;
   }
   else{}
  
 
   // Compute the velocity
   //odomNew.header.stamp = ros::Time::now();
   odomNew.twist.twist.linear.x = V;  //cycledistance_Rob/(odomNew.header.stamp.toSec() - odomOld.header.stamp.toSec());
   odomNew.twist.twist.angular.z = Fi_dot;  //cycleAngle/(odomNew.header.stamp.toSec() - odomOld.header.stamp.toSec());
   ROS_INFO_STREAM("V = odomNew.twist.twist.linear.x ="<<odomNew.twist.twist.linear.x);
   ROS_INFO_STREAM("Fi_dot = odomNew.twist.twist.angular.z ="<<odomNew.twist.twist.angular.z);

 
   // Save the pose data for the next cycle
   odomOld.pose.pose.position.x = odomNew.pose.pose.position.x;
   odomOld.pose.pose.position.y = odomNew.pose.pose.position.y;
   odomOld.pose.pose.orientation.z = odomNew.pose.pose.orientation.z;
   odomOld.header.stamp = odomNew.header.stamp;
  
   // Publish the odometry message
   odom_data_pub.publish(odomNew);
 */
}     




int main(int argc, char **argv)	{

ros::init(argc, argv, "eigen");
ros::NodeHandle node; 

ros::Subscriber subOdom = node.subscribe("sickLidarOdom", 10, LidarLocPose, ros::TransportHints().tcpNoDelay());
ros::Subscriber subWozek_Vw = node.subscribe("servo_vel_kola", 10, GetWozek_Vw,  ros::TransportHints().tcpNoDelay());
ros::Subscriber subWozek_Psi = node.subscribe("servo_Psi_kola", 10, GetWozek_Psi, ros::TransportHints().tcpNoDelay());

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

/*Lidar_x_pub = node.advertise<std_msgs::Float32>("Lidar_x_msgs", 10);
Lidar_y_pub = node.advertise<std_msgs::Float32>("Lidar_y_msgs", 10);
Lidar_Fi_pub = node.advertise<std_msgs::Float32>("Lidar_Fi_msgs", 10);

Wozek_Vw_pub = node.advertise<std_msgs::Float32>("Wozek_Vw_msgs", 10);
Wozek_Psi_pub = node.advertise<std_msgs::Float32>("Wozek_Psi_msgs", 10);

x1_pub = node.advertise<std_msgs::Float32>("x1_msgs", 10);
x2_pub = node.advertise<std_msgs::Float32>("x2_msgs", 10);
x3_pub = node.advertise<std_msgs::Float32>("x3_msgs", 10);*/

// x_k for t=0
//x_k	<<	0.0,	0.0,	0.0;
x_k	<<	Lidar_x,	Lidar_y,	Lidar_Fi;

ros::Rate loop_rate(1);

A	<< 	1.0,	0,		0,
 			0,		1.0,	0,
 			0,		0,		1.0; 

H	<<		1.0,	0,		0,
 			0,		1.0,	0,
 			0,		0,		1.0;
				
P_k	<<	10000000.1,	0,			0,
         0,			10000000.1,	0,
         0,			0,				10000000.1;
         
R_k	<<	0.1,	0,		0,
 			0,		0.1,	0,
 			0,		0,		0.1;  

Q_k	<<	0.1,	0,		0,
			0,		0.1,	0,
			0,		0,		0.1;
			
  				


  while (ros::ok())
  {
	
	/*Lidar_x_msgs.data = Lidar_x;
   Lidar_x_pub.publish((std_msgs::Float32)Lidar_x_msgs); 
	Lidar_y_msgs.data = Lidar_y;
   Lidar_y_pub.publish((std_msgs::Float32)Lidar_y_msgs);
   Lidar_Fi_msgs.data = Lidar_Fi;
   Lidar_y_pub.publish((std_msgs::Float32)Lidar_y_msgs);*/
   
   /*Wozek_Vw_msgs.data = Wozek_Vw;
   Wozek_Vw_pub.publish((std_msgs::Float32)Wozek_Vw_msgs);
   Wozek_Psi_msgs.data = Wozek_Psi;
   Wozek_Psi_pub.publish((std_msgs::Float32)Wozek_Psi_msgs);*/
  // Publisher of simple odom message where orientation.z is an euler angle
  //odom_data_pub = node.advertise<nav_msgs::Odometry>("odom", 30);
  
  
  update_odom();
  //odom_generator();
  
  
  



    ros::spinOnce();
    loop_rate.sleep();
   
  }
  return 0;
}
