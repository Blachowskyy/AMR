#!/usr/bin/env python3
from time import sleep
from pyModbusTCP import client
import rospy
from std_msgs.msg import Int64, Float32, Bool, Int32, String
class ForkliftSensors:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        #float
        self.servo_angle = 0.0
        self.battery_voltage = 0.0
        self.OldBatteryVoltage = 0.0
        #int64
        self.battery_percentage = 0
        self.OldBatteryPercentage = 0
        self.servo_direction = 0
        self.current_workstate = 0
        self.forks_height = 0
        self.cargo_weight = 0
        self.tilt_axis_1 = 0
        self.tilt_axis_2 = 0
        self.tilt_offset = 180
        self.current_speed = 0.0
        #bool
        self.forks_limiter = False
        self.battery_critical_state = False
        #refresh rate
        self.rate = rospy.Rate(30) # 10Hz
        #log saver
        self.log_message = ''
        self.log_level = 0
        self.DistanceNow = 0
        self.DistanceLast = 0
        self.DistanceTraveledKM = 0.0
        self.DistanceTraveledM = 0.0
        self.DistanceTraveledMM = 0.0
        while not rospy.is_shutdown():
            try:
                #Subscriber's
                self.tilt_axis_1_sub = rospy.Subscriber('PLC/read/tilt_axis_1', Int64, self.tilt_axis_1_read)
                self.tilt_axis_2_sub = rospy.Subscriber('PLC/read/tilt_axis_2', Int64, self.tilt_axis_2_read)
                self.battery_voltage_sub = rospy.Subscriber('PLC/read/battery_voltage', Int64, self.battery_voltage_read)
                self.servo_direction_sub = rospy.Subscriber('PLC/read/servo_direction', Int64, self.servo_direction_read)
                self.servo_angle_sub = rospy.Subscriber('PLC/read/servo_angle', Int64, self.servo_angle_read)
                self.current_speed_sub = rospy.Subscriber('PLC/read/encoder_speed', Int64, self.current_speed_read)
                self.forks_height_limiter_sub = rospy.Subscriber('PLC/read/forks_height_limiter', Int64, self.fork_height_limit_read)
                self.forks_height_sub = rospy.Subscriber('PLC/read/fork_height', Int64, self.fork_height_read)
                self.cargo_weight_sub = rospy.Subscriber('PLC/read/cargo_weight', Int64, self.cargo_weight_read)
                self.DistanceReadSub = rospy.Subscriber('PLC/read/distance', Int64, self.DistanceReadCallback)
                #publisher's
                self.tilt_axis_1_pub = rospy.Publisher('Forklift/sensors/tilt_axis_1', Int64, queue_size=1)
                self.tilt_axis_2_pub = rospy.Publisher('Forklift/sensors/tilt_axis_2', Int64, queue_size=1)
                self.battery_voltage_pub = rospy.Publisher('Forklift/state/battery_voltage', Float32, queue_size=1, latch=True)
                self.battery_percentage_pub = rospy.Publisher('Forklift/state/battery_percentage', Float32, queue_size=1, latch=True)
                self.battery_critical_pub = rospy.Publisher('Forklift/state/battery_critical_state', Bool, queue_size=1)
                self.servo_angle_pub = rospy.Publisher('Forklift/drive/current_servo_angle', Float32, queue_size=1)
                # self.current_speed_pub = rospy.Publisher('Forklift/drive/actual_speed', Float32, queue_size=1)
                self.cargo_weight_pub = rospy.Publisher('Forklift/forks/cargo_weight', Int64, queue_size=1)
                self.forks_height_pub = rospy.Publisher('Forklift/forks/forks_height', Int64, queue_size=1)
                self.forks_height_lim_pub = rospy.Publisher('Forklift/forks/height_limiter', Bool, queue_size=1)
                self.log_message_pub = rospy.Publisher('log/message', String, queue_size=10)
                self.log_level_pub = rospy.Publisher('log/level', Int32, queue_size=10)
                self.MMPub = rospy.Publisher('Forklift/drive/distance/mm', Float32, queue_size=1)
                self.MPub = rospy.Publisher('Forklift/drive/distance/m', Float32, queue_size=1)
                self.KMPub = rospy.Publisher('Forklift/drive/distance/km', Float32, queue_size=1)
                
            except(rospy.ServiceException, rospy.ROSException) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
            self.publishing()
    def DistanceReadCallback(self, msg):
        self.DistanceNow = msg.data
    def current_speed_read(self, msg):
        speed = msg.data
        self.current_speed = speed / 100
    def tilt_axis_1_read(self, msg):
        #Odczyt czujnika przechylu - os 1
        tilt = msg.data
        self.tilt_axis_1 = tilt - self.tilt_offset
    def tilt_axis_2_read(self, msg):
        #Odczyt czujnika przechylu - os 2
        tilt = msg.data
        self.tilt_axis_2 = tilt - self.tilt_offset
    def battery_voltage_read(self, msg):
        #Odczyt poziomu baterii
        battery_tmp = msg.data # RAW data
        self.battery_voltage = battery_tmp / 100 # zmiana odczytu na float xx,xx V
        battery_tmp2 = 100 - ((28.0 - self.battery_voltage) / 0.0743) # Konwersja odczytu na procenty
        self.battery_percentage = round(battery_tmp2, 2) #Zaokraglenie procent baterii do 2 miejsc po przecinku
        #Warunki bledu obliczen, aby % baterii nie przekroczyl 100 i nie spadl ponizej 0 
        if self.battery_percentage > 100:
            self.battery_percentage = 100
        if self.battery_percentage <= 0:
            self.battery_percentage = 0
        #Warunek i wyznaczenie krytycznego stanu baterii ( na wstepie ustalone 15 % )
        if self.battery_percentage < 15:
            self.battery_critical_state = True
        else:
            self.battery_critical_state = False   
    def servo_direction_read(self, msg):
        #Odczyt aktualnego kierunku katu skretu kolka ( nie odczytujemy znaku przy kacie skretu )
        self.servo_direction = msg.data
    def servo_angle_read(self, msg):
        #Odczyt aktualnego kata skretu
        angle = msg.data #RAW data
        angle2 = angle / 100 # Na liczbe zmiennoprzecinkowa
        #Warunki na ewentualna zmiane znaku ( def servo_direction_read )
        if self.servo_direction == 1:
            angle2 = -angle2
        if self.servo_direction == 2:
            angle2 = angle2
        #Zapisanie aktualnego kata uwzgledniajac znaki
        self.servo_angle = angle2
    # def current_work_state_read(self, msg):
        #Odczyt aktualnego stanu pracy wozka
        # self.current_workstate = msg.data
    def fork_height_read(self, msg):
        #Odczyt wysokosci widel
        self.forks_height = msg.data
    def cargo_weight_read(self, msg):
        #Odczyt obciazenia czujnika cisnienia ( waga na widlach )
        self.cargo_weight = msg.data
    def fork_height_limit_read(self, msg):
        #Odczyt stanu czujnika krancowego podnoszenia widel
        forks_lim_tmp = msg.data
        #Konwersja odczytanej liczby na bool
        if forks_lim_tmp == 0:
            self.forks_limiter = False
        elif forks_lim_tmp == 1:
            self.forks_limiter = True
        else:
            self.forks_limiter = None
            rospy.loginfo('err')
    def publishing(self):
        distanceDifference = self.DistanceNow - self.DistanceLast
        if distanceDifference == 0:
            distanceToAdd = 0
        if distanceDifference < 0:
            distanceToAdd = (65535 - self.DistanceLast) + self.DistanceNow
        if distanceDifference > 0:
            distanceToAdd = distanceDifference
        rospy.loginfo(f'Dodaje dystans : {distanceToAdd}')
        self.DistanceTraveledMM = self.DistanceTraveledMM + distanceToAdd
        self.DistanceTraveledM = self.DistanceTraveledM + (distanceToAdd / 1000)
        self.DistanceTraveledKM = self.DistanceTraveledKM + (distanceToAdd / 1000000)
        self.MMPub.publish(self.DistanceTraveledMM)
        self.MPub.publish(self.DistanceTraveledM)
        self.KMPub.publish(self.DistanceTraveledKM)
        self.DistanceLast = self.DistanceNow
        #Publikacja dostosowanych zmiennych wozka
        self.tilt_axis_1_pub.publish(self.tilt_axis_1)
        self.tilt_axis_2_pub.publish(self.tilt_axis_2)
        if self.battery_voltage - self.OldBatteryVoltage > 0.1 :
            self.battery_voltage_pub.publish(self.battery_voltage)
        if self.battery_percentage - self.OldBatteryPercentage > 0.1:
            self.battery_percentage_pub.publish(self.battery_percentage)
        self.battery_critical_pub.publish(self.battery_critical_state)
        self.servo_angle_pub.publish(self.servo_angle)
        # self.current_speed_pub.publish(self.current_speed)
        self.cargo_weight_pub.publish(self.cargo_weight)
        self.forks_height_pub.publish(self.forks_height)
        self.forks_height_lim_pub.publish(self.forks_limiter)
        rospy.loginfo('++++++++++ SENSORS LOOP +++++++')
        self.rate.sleep()
                    
if __name__ == '__main__':
    try:    
        rospy.init_node('forklift_sensors')
        forklift_sensors = ForkliftSensors()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        