 #!/usr/bin/env python3

import requests
import rospy
from std_msgs.msg import String

def instr():
    pub = rospy.Publisher('instruction_from_api', String, queue_size=50)
    rospy.init_node('instr', anonymous=True)
    rate = rospy.Rate(1) # 1hz
    rospy.loginfo("Publisher Delta Started")

    URL = "http://192.168.3.38:2137/app/instruction"
    
    while not rospy.is_shutdown():
        r = requests.get(URL)
        msg = r.json()
        rospy.loginfo(msg)
        pub.publish(msg)
        rate.sleep()

if __name__ == '__main__':
    instr()