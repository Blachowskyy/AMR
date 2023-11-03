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
#include <geometry_msgs/Pose2D.h>
#include <geometry_msgs/PoseStamped.h>
#include <geometry_msgs/TransformStamped.h>
//#include <tf2/LinearMath/Quaternion.h>
#include <tf/transform_broadcaster.h>
#include <cmath>
#include "sick_lidar_localization/LocalizationControllerResultMessage0502.h"
#include <sstream>
#include <eigen3/Eigen/Dense>

using namespace std;
using std::vector;
using Eigen::MatrixXd;
using Eigen::VectorXd;


 
// Create odometry data publishers
ros::Publisher odom_data_pub;
//ros::Publisher odom_data_pub_quat;
ros::Publisher sickLidarPose2D_pub;
ros::Publisher odomPose2D_pub;

//ros::Publisher comand_curtis_vel_pub;
//ros::Publisher comand_servo_angle_pub;
nav_msgs::Odometry odomNew;
nav_msgs::Odometry odomOld;
nav_msgs::Odometry sickLidarOdom;
std_msgs::Int64 PWM_DutyCycle;
std_msgs::Int64 ServoTick;
geometry_msgs::Pose2D odomPose2D;
geometry_msgs::Pose2D sickLidarPose2D;


//ros::Publisher Lidar_x_pub;
//ros::Publisher Lidar_y_pub;
//ros::Publisher Lidar_Fi_pub;

//ros::Publisher Wozek_Vw_pub;
//ros::Publisher Wozek_Psi_pub;

//ros::Publisher x1_pub;
//ros::Publisher x2_pub;
//ros::Publisher x3_pub;


tf::TransformBroadcaster *tb;
 

  
  
Eigen::Matrix3d A;
Eigen::Matrix3d A_T;
Eigen::MatrixXd B_k_1(3, 2);			
Eigen::Matrix3d H;
Eigen::Matrix3d H_T; 		
Eigen::Matrix3d R_k;
Eigen::Matrix3d Q_k;
Eigen::Matrix3d K_k;
Eigen::Matrix3d S_k;
Eigen::Matrix3d invS_k;
Eigen::Matrix3d P_k;
Eigen::Vector3d x_k;
Eigen::Vector3d x_k1;
Eigen::Vector3d x_dot;
Eigen::Vector3d y_k;
Eigen::Vector3d y_k1;
Eigen::Vector2d u_k_1;
Eigen::Vector3d w_k;
Eigen::Vector3d v_k; 

// Initial pose
const double initialX = 0.0;
const double initialY = 0.0;
const double initialFi = 0.0;
const double PI = 3.141592;
 
// Robot physical constants
const double WHEEL_RADIUS = 0.105; 	// Wheel radius in meters
const double BASE = 1.195; 		//?// Center of turning to direction tire

double DeltaTime = 0, TimeOld = 0, Czas=0;
double Vw=0, V=0, Psi = 0, Fi=0, Lidar_x=0, Lidar_y=0, Lidar_Fi=0;
double X_dot=0, Y_dot=0, Fi_dot=0;
double x=0, y=0, fi=0, Wozek_Vw=0, Wozek_Psi=0;
double d_t=0.0;
long time_i = 0;
int ii = 1;
int iii = 0;
// Flag to see if initial pose has been received
bool initialPoseRecieved = false;
 
/*
void odom_generator()		{

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
  ROS_INFO_STREAM("DeltaTime = "<<DeltaTime);
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

 
// Get initial_2d message from either Rviz clicks or a manual pose publisher
void set_initial_2d(const geometry_msgs::PoseStamped &rvizClick) {
 
  odomOld.pose.pose.position.x = rvizClick.pose.position.x;
  odomOld.pose.pose.position.y = rvizClick.pose.position.y;
  odomOld.pose.pose.orientation.z = rvizClick.pose.orientation.z;
  initialPoseRecieved = true;
}


// Calculate the distance_Rob the wheel has traveled since the last cycle
void GetVw(const std_msgs::Float32& Velocity) {
              
  Wozek_Vw = Velocity.data;
  ROS_INFO_STREAM(" Wozek_Vw= "<< Wozek_Vw);
}

void GetPsi(const std_msgs::Float32& Angle) {

  Wozek_Psi = Angle.data;
  //ROS_INFO_STREAM(" Wozek_Psi = "<<Wozek_Psi );
}

// Take angle from LidarLoc
void LidarLocPose(const sick_lidar_localization::LocalizationControllerResultMessage0502 &msg) {
  //ROS_INFO("LidarLocPose");

    Lidar_x = msg.x/1000.0;
    Lidar_y = msg.y/1000.0;
    Lidar_Fi = ((msg.heading/1000.0) * PI)/180.0;
    
    

    sickLidarPose2D.x = Lidar_x;
    sickLidarPose2D.y = Lidar_y;
    sickLidarPose2D.theta = Lidar_Fi;

   
    sickLidarPose2D_pub.publish(sickLidarPose2D);


    //ROS_INFO_STREAM("x= "<< x <<" y= "<< y <<" yaw= "<<yaw);
    //ROS_INFO_STREAM("nav x= "<< sickOdom.pose.pose.position.x <<" nav y= "<< sickOdom.pose.pose.position.y <<" nav yaw= "<<sickOdom.pose.pose.orientation.z);
}



void update_trans() {

  //ROS_INFO("update transform");

 // transform message declarations
  tb = new tf::TransformBroadcaster();
  geometry_msgs::TransformStamped transformStamped;
  transformStamped.header.frame_id = "odom";
  transformStamped.child_frame_id = "base_footprint";
  
  
//   // update transform
 	transformStamped.header.stamp = ros::Time::now(); 
 	transformStamped.transform.translation.x = odomNew.pose.pose.position.x;
 	transformStamped.transform.translation.y = odomNew.pose.pose.position.y; 
 	transformStamped.transform.translation.z = 0.0;
 	transformStamped.transform.rotation = tf::createQuaternionMsgFromYaw(odomPose2D.theta);
  //transformStamped.transform.rotation.x = odomNew.pose.pose.orientation.x;
  //transformStamped.transform.rotation.y = odomNew.pose.pose.orientation.y;
  //transformStamped.transform.rotation.z = odomNew.pose.pose.orientation.z;
  //transformStamped.transform.rotation.w = odomNew.pose.pose.orientation.w;
 	tb->sendTransform(transformStamped);	
 }
 

 
// Update odometry information
void update_odom() {


  //ROS_INFO("update_odom");
  odomNew.header.stamp = ros::Time::now();
  if (ii == 1)	{
   TimeOld = odomNew.header.stamp.toSec();  
   ii=2; 
   //ROS_INFO("ii=2");
  }
  else	{}
   
   
   // Calculate the time step
   DeltaTime = (odomNew.header.stamp.toSec() - TimeOld);
   TimeOld = odomNew.header.stamp.toSec();
   
//odom_generator();  

d_t=DeltaTime;
//ROS_INFO_STREAM("d_t= "<< d_t );
//ROS_INFO_STREAM("Lidar_x="<< Lidar_x << " # Lidar_y="<< Lidar_y<< " # Lidar_Fi="<< Lidar_Fi );


if ((d_t != 0)	&& ((Lidar_x != 0) || (Lidar_y != 0)|| (Lidar_Fi != 0)))	{


u_k_1(0,0)	= 	Wozek_Vw * cos(Wozek_Psi);				//V + v_k;
u_k_1(1,0)	= Wozek_Vw * (sin(Wozek_Psi)/BASE);		//Fi_dot + v_k
//ROS_INFO_STREAM("u V_dot= "<< u_k_1(0,0)<<" u Fi_dot= "<< u_k_1(1,0) );
y_k	<<	Lidar_x,	Lidar_y,	Lidar_Fi;
//ROS_INFO_STREAM("Y x= "<< y_k(0,0)<<" Y y= "<< y_k(1,0) <<" Y yaw= "<<y_k(2,0));
Fi = Fi + (d_t * u_k_1(1,0));

//ROS_INFO_STREAM("Fi = " << Fi);


B_k_1	<<		cos(Fi)*d_t,	0,
         	sin(Fi)*d_t,	0,
         	0,	d_t;
         	
         	
// std::cout <<"B_k_1 = "<< B_k_1 << std::endl;
//Predict the state estimate at time k based on the state 

// x_k = A * x_k + B_k_1 * u_k_1 + v_k;
x_k = A * x_k + B_k_1 * u_k_1;
//ROS_INFO_STREAM("1 x_k= "<< x_k(0,0)<<" x_k= "<< x_k(1,0) <<" x_k= "<< x_k(2,0) );

// y_k = H * x_k + w_k;


//Calculate the model residual covariance
// A_T = A.transpose();
A_T = A;
P_k =  A * P_k * A_T + Q_k;
//Calculate the measurement residual covariance
// H_T = H.transpose();
H_T = H;
S_k = H * P_k * H_T + R_k;
invS_k = S_k.inverse();

K_k = P_k * H_T * invS_k;

//std::cout << K_k << std::endl;
// y_k(2,0) = y_k(2,0) * (-1)
//Estimation

P_k =  P_k - K_k * H * P_k;
x_k = x_k + K_k * (y_k - H * x_k);
ROS_INFO_STREAM("Lidar_x="<< Lidar_x << "  x_k= "<< x_k(0,0)<< " # Lidar_y="<< Lidar_y<< "  y_k="<< x_k(1,0) << " # Lidar_Fi="<< Lidar_Fi << " Fi_k="<< x_k(2,0));






//x_k = y_k;      //@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2
//the position 
double X = x_k(0,0);
double Y = x_k(1,0);
double Fi = x_k(2,0);


// The new pose (x, y, and fi)
odomNew.pose.pose.position.x = X;
odomNew.pose.pose.position.y = Y;
odomNew.pose.pose.position.z = 0.0;
geometry_msgs::Quaternion odom_quat = tf::createQuaternionMsgFromYaw(Fi);
odomNew.pose.pose.orientation = odom_quat;


// Velocity Estimation





//x_k1 = x_k;
             //@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2
if (iii == 0){
  x_k1 = x_k;
  iii = 2;
  ROS_INFO_STREAM("iii = 0");
}
else {
   ROS_INFO_STREAM("iii = cos");
}

if ((x_dot(2,0) - x_k1(2,0)) > abs(PI/2))
{}
else  {
  x_dot = (x_k -x_k1) / d_t; }
x_k1 = x_k;

ROS_INFO_STREAM("x_dot="<<  x_dot(0,0)<< " # y_dot="<< x_dot(1,0)<< "  # Fi_dot="<< x_dot(2,0));
//Data filtration
  float alfa = 0.7;
  X_dot = alfa * X_dot + (1 - alfa) * x_dot(0,0);
  Y_dot = alfa * Y_dot + (1 - alfa) * x_dot(1,0);
  Fi_dot = alfa * Fi_dot + (1 - alfa) * x_dot(2,0);
ROS_INFO_STREAM("Po filtracji X_dot = "<<X_dot<<" Y_dot= "<<Y_dot<<" Fi_dot= "<<Fi_dot);
 
// Prevent lockup from a single bad cycle
if (isnan(odomNew.pose.pose.position.x) || isnan(odomNew.pose.pose.position.y)
  || isnan(odomNew.pose.pose.position.z)) {
  odomNew.pose.pose.position.x = odomOld.pose.pose.position.x;
  odomNew.pose.pose.position.y = odomOld.pose.pose.position.y;
  odomNew.pose.pose.orientation = odomOld.pose.pose.orientation;
 }

for(int i = 0; i<36; i++) {
    if(i == 0 || i == 7 || i == 14) {
      odomNew.pose.covariance[i] = .01;
     }
     else if (i == 21 || i == 28 || i== 35) {
       odomNew.pose.covariance[i] += 0.1;
     }
     else {
       odomNew.pose.covariance[i] = 0;
     }
  }

  odomPose2D.x = odomNew.pose.pose.position.x;
  odomPose2D.y = odomNew.pose.pose.position.y;
  tf::Quaternion q(
        odomNew.pose.pose.orientation.x,
        odomNew.pose.pose.orientation.y,
        odomNew.pose.pose.orientation.z,
        odomNew.pose.pose.orientation.w);
    tf::Matrix3x3 m(q);
    double roll, pitch, yaw;
    m.getRPY(roll, pitch, yaw);
    
    odomPose2D.theta = yaw;
    odomPose2D_pub.publish(odomPose2D);



 
// Make sure theta stays in the correct range
if (odomPose2D.theta > PI) {
  odomPose2D.theta -= 2 * PI;
}
else if (odomPose2D.theta < -PI) {
  odomPose2D.theta += 2 * PI;
}
else{}

// The new velocity
//odomNew.header.stamp = ros::Time::now();
odomNew.twist.twist.linear.x = X_dot;  
odomNew.twist.twist.linear.y = Y_dot;
odomNew.twist.twist.angular.z = Fi_dot; 

ROS_INFO_STREAM("X = odomPose2D.x="<<odomPose2D.x);
ROS_INFO_STREAM("Y = odomPose2D.x="<<odomPose2D.y);
ROS_INFO_STREAM("Fi = odomPose2D.x="<<odomPose2D.theta);
 
ROS_INFO_STREAM("Vx = odomNew.twist.twist.linear.x ="<<odomNew.twist.twist.linear.x);
ROS_INFO_STREAM("Vy = odomNew.twist.twist.linear.y ="<<odomNew.twist.twist.linear.y);
ROS_INFO_STREAM("Fi_dot = odomNew.twist.twist.angular.z ="<<odomNew.twist.twist.angular.z);

 
//   // Save the pose data for the next cycle
odomOld.pose.pose.position.x = odomNew.pose.pose.position.x;
odomOld.pose.pose.position.y = odomNew.pose.pose.position.y;
odomOld.pose.pose.orientation = odomNew.pose.pose.orientation;
odomOld.header.stamp = odomNew.header.stamp;
  
// Publish the odometry message
odom_data_pub.publish(odomNew);



}
else{}


}

// Update odometry information
// void update_odom() {

//   ROS_INFO("update_odom");

//   odomNew = sickOdom;
//   odomNew.header.stamp = ros::Time::now();
//   odomNew.header.frame_id = "odom";
//   odomNew.child_frame_id = "base_link";
  
//   // Publish the odometry message
//   odom_data_pub.publish(odomNew);

// }



int main(int argc, char **argv) {
 
 // Launch ROS and create a node
  ros::init(argc, argv, "odom_pub1");
  ros::NodeHandle node;  
  

  // Set the data fields of the odometry message
  odomNew.header.frame_id = "odom";
  //odomNew.header.stamp = ros::Time::now();;
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
  odomOld.pose.pose.orientation.z = initialFi;
  iii = 0;

  // x_k for t=0
x_k	<<	initialX,	initialY,	initialFi;
x_k1	<<	initialX,	initialY,	initialFi;
x_dot	<<	0.0,	0.0,	0.0;



A	<< 	1.0,	0,		0,
 			0,		1.0,	0,
 			0,		0,		1.0; 

H	<<	1.0,	0,		0,
 			0,		1.0,	0,
 			0,		0,		1.0;
				
P_k	<<	100.1,	0,		  0,
         0,		  100.1,	0,
         0,		  0,		  100.1;
         
R_k	<<	0.1,	0,		0,
 			  0,		0.1,	0,
 			  0,		0,		0.1;  

Q_k	<<	0.1,	0,		0,
			  0,		0.1,	0,
			  0,		0,		0.1;
			
  				
  
   
  // Subscribe to ROS topics
  //ros::Subscriber subForTickCounts = node.subscribe("wozek_angle_tick", 30, DistanceCalc,  ros::TransportHints().tcpNoDelay());
  //ros::Subscriber subForAngeCounts = node.subscribe("servo_angle_tick", 30, AngleCalc, ros::TransportHints().tcpNoDelay());  
  ros::Subscriber subInitialPose = node.subscribe("initial_2d", 1, set_initial_2d);
  ros::Subscriber subLidarLocPose = node.subscribe("localizationcontroller/out/localizationcontroller_result_message_0502", 30, LidarLocPose);
  ros::Subscriber subForTickCounts = node.subscribe("servo_vel_kola", 1, GetVw,  ros::TransportHints().tcpNoDelay());
  ros::Subscriber subForAngeCounts = node.subscribe("servo_Psi_kola", 1, GetPsi, ros::TransportHints().tcpNoDelay());  
 

  odom_data_pub = node.advertise<nav_msgs::Odometry>("odom", 1);
  // Publisher of full odom message where orientation is quaternion
  //odom_data_pub_quat = node.advertise<nav_msgs::Odometry>("odom_data_quat", 1);
  sickLidarPose2D_pub = node.advertise<geometry_msgs::Pose2D>("sickLidarPose2D", 1);
  odomPose2D_pub =  node.advertise<geometry_msgs::Pose2D>("odomPose2D", 1);
  
  //comand_curtis_vel_pub = node.advertise<std_msgs::Int64>("comand_curtis_vel", 30);
  //comand_servo_angle_pub = node.advertise<std_msgs::Int64>("comand_servo_angle", 30);
  
 
  //ros::Time::init();
  //ros::Rate loop_rate(100); 
  ros::Rate loop_rate(10);   
  while(ros::ok()) {
      
   // if(initialPoseRecieved) {
    ROS_INFO("LOOP");
      update_odom();
      //publish_quat();
      update_trans();
      
      
     
    ros::spinOnce();
    loop_rate.sleep();
  }
 
  return 0;
}

