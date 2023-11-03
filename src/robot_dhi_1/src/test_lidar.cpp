#include "ros/ros.h"
#include "sick_lidar_localization/LocalizationControllerResultMessage0502.h"
#include <cstdio>
#include <string>



void LidarLocPose(const sick_lidar_localization::LocalizationControllerResultMessage0502 &msg) {
    long int Tick = msg.heading;
    ROS_INFO_STREAM("heading="<<Tick);
}

int main(int argc, char **argv) {
    ros::init(argc, argv, "test_lidar");
    ros::NodeHandle nh;

    ros::Subscriber subLidarLocPose = nh.subscribe("localizationcontroller/out/localizationcontroller_result_message_0502", 1000, LidarLocPose);

    ros::spin();

    return 1;
}