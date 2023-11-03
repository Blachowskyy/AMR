import rospy
from sick_lidar_localization.msg import LocalizationControllerResultMessage0502


def callback(data):
    loc_status = int(data.loc_status)
    rospy.loginfo("loc_status"+ str(loc_status))
    map_match_status = int(data.map_match_status)
    rospy.loginfo("map_match_status"+str(map_match_status))

def main():
    rospy.init_node('debug_lidarlock')
    rospy.loginfo('oki')
    rospy.Subscriber('/localizationcontroller/out/localizationcontroller_result_message_0502',LocalizationControllerResultMessage0502, callback)

if __name__ == '__main__':
    main()