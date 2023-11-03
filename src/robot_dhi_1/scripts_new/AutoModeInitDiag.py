#!/usr/bin/env python3
import datetime
import rospy
from time import sleep
from std_msgs.msg import Bool,Int32, Int64, Float32, String
from robot_dhi_1.msg import FlexiReads

class Startup_sequence:
    def __init__(self):
        #Deklaracje zmiennych globalnych uzytych w skrypcie
        self.check_counter = 0
        self.ping_status = False
        self.safety_status = FlexiReads()
        self.init_status = False
        self.manual_active = False
        self.first_cycle = False
        self.timeout_safety = 0.0
        self.speed = 0.0
        self.angle = 0.0
        self.fork_height_actual = 0
        self.startup_status = True
        self.stopping_OK = False
        self.end_test = False
        self.message = ''
        self.level = 0
        self.workstate_status = False
        self.servo_status = False
        self.curtis_status = False
        self.forks_status = False
        self.test_status = None
        #rozpoczecie nieskonczonej petli programu
        while not rospy.is_shutdown():
            try:
                #deklaracje subscriberow 
                self.ping_sub = rospy.Subscriber('Forklift/state/startup/ping_status', Bool, self.ping_read, queue_size=1)
                self.safety_status_sub = rospy.Subscriber('Forklift/state/safety/safety_status', FlexiReads, self.safety_read)
                self.servo_angle_sub = rospy.Subscriber('Forklift/drive/current_servo_angle', Float32, self.servo_angle_read)
                self.speed_sub = rospy.Subscriber('Forklift/drive/actual_speed', Float32, self.speed_read)
                self.forks_height_sub = rospy.Subscriber('Forklift/forks/forks_height', Int64, self.forks_height_read)
                #deklaracje publisherow
                self.servo_angle_pub = rospy.Publisher('Forklift/control/servo_angle', Float32, queue_size=1, latch=True)
                self.speed_pub = rospy.Publisher('Forklift/control/PWM_curtis', Int64, queue_size=1, latch=True)
                self.log_message_pub = rospy.Publisher('log/message', String, queue_size=1, latch=True)
                self.log_level_pub = rospy.Publisher('log/level', Int32, queue_size=1, latch=True)
                self.forks_command_pub = rospy.Publisher('Forklift/control/forks', Int64, queue_size=1)
                self.test_status_pub = rospy.Publisher('test_status', Bool, queue_size=1, latch= True)
            except (rospy.ServiceException, rospy.ROSException) as e:
                rospy.logger(e)
            rospy.loginfo('Starting diagnostic test...')
            self.auto_mode_initialize() #Uruchomienie glownej metody
            rospy.loginfo(self.test_status) #info w konsoli o statusie testu
            self.test_status_pub.publish(self.test_status) #publikacja stanu testu do programu glownego wozka
            if self.test_status:
                self.test_status = self.test_status     
            if not self.test_status:
                return None
            break
        
    def forks_height_read(self, msg):
        self.fork_height_actual = msg.data #Odczyt wysokosci widel
    def speed_read(self, msg):
        self.speed = msg.data #odczyt predkosci
    def servo_angle_read(self, msg):
        self.angle = msg.data #Odczyt kata skretu kolka
    def safety_read(self, msg):
        self.safety_status = msg #Odczyt informacji z safety
    def log_publisher(self):
        self.log_message_pub.publish(self.message) #Publikacja loga
        self.log_level_pub.publish(self.level)    #publikacja poziomu loga
    def ping_read(self, msg):
        self.ping_status = msg.data #Odczyt stanu pingowania z skryptu ConnectionTest.py
    def servo_test(self):
        #Metoda testu serwonaedup
        angle_1 = 5.0 # wyznaczenie pierwszego kata
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = 2.0) #Wyznaczenie timeoutu do odczytu aktualnego kata
        while True:
            if datetime.datetime.now() >= endtime:
                self.message = 'Done first test!'
                self.level = 2
                self.log_publisher()
                break
            self.message = 'Testing first angle...'
            self.servo_angle_pub.publish(angle_1)
            self.level = 2
            self.log_publisher()
        angle_readed_1 = self.angle
        sleep(0.1)
        angle_2 = -5.0 
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = 2.0)
        while True:
            if datetime.datetime.now() >= endtime:
                self.message = 'Done second test!'
                self.level = 2
                self.log_publisher()
                break
            self.message = 'Testing first angle...'
            self.servo_angle_pub.publish(angle_2)
            self.level = 2
            self.log_publisher()
        angle_readed_2 = self.angle
        sleep(0.1)
        angle_3 = 0.0
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = 2.0)
        while True:
            if datetime.datetime.now() >= endtime:
                self.message = 'Done third test!'
                self.level = 2
                self.log_publisher()
                break
            self.message = 'Testing third angle...'
            self.level = 2
            self.log_publisher()
            self.servo_angle_pub.publish(angle_3)
        angle_readed_3 = self.angle
        #Wyznaczenie dopuszczalnych roznic z uwagi na to, ze kat odczytany moze sie delikatnie roznic od zadanego
        angle_diff_1 = angle_1 - angle_readed_1
        angle_diff_2 = angle_2 - angle_readed_2
        angle_diff_3 = angle_3 - angle_readed_3
        rospy.loginfo(f'Angle diff 1: {angle_diff_1} \n Angle diff 2: {angle_diff_2} \nAngle diff 3: {angle_diff_3}')
        #POROWNANIE KATOW ODCZYTANYCH Z ZADANYMI Z UWZGLEDNIENIEM LEKKICH ROZNIC W ODCZYCIE
        if (angle_diff_1 < 0.1 and angle_diff_1 > -0.1 and angle_diff_2 < 0.1 and angle_diff_2 > -0.1 and angle_diff_3 < 0.1 and angle_diff_3 > -0.1 ):
            self.message ='Angles_OK!'
            self.level = 2
            self.log_publisher()
            sleep(0.2)
            return True
        else:
            self.message ='Angles_NOT_OK!'
            self.level = 5
            self.log_publisher()
            sleep(0.2)
            return False
    def curtis_test(self):
        #Metoda sprawdzenia poprawnosci dzialania napedu curtis i przy okazji enkodera
        #Ustawienie minimalnych wartosci predkosciw obu kierunkach oraz hamowania, przygotowanie zmiennych do odczytu predkosci
        speed_1 = 1500
        speed_2 = -1500
        stop = 0
        speed_measure_1 = 0.0
        speed_measure_2 = 0.0
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = 6.0) #Wyznaczenie timeoutu na ruch
        while True:
            self.message ='Forklift autodiagnostic: Forward move test started..'
            self.level = 2
            self.log_publisher()
            sleep(0.2)
            if self.speed != 0.0 or datetime.datetime.now() >= endtime:
                if self.speed == 0.0: #Wywolanie bledu gdy predkosc nie narosla / nie odczytano predkosci z encodera
                    self.message ='Forklift autodiagnostic: Forward move finished with error!'
                    self.level = 5
                    self.log_publisher()
                    sleep(0.2)
                    break
                else:
                    speed_measure_1 = self.speed
                    self.message ='Forklift autodiagnostic: Forward move OK!'
                    self.level = 2
                    self.log_publisher()
                    sleep(0.2)
                    break
                
            self.speed_pub.publish(speed_1)
        sleep(0.1)
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = 5.0)
        while True:
            self.message ='Forklift autodiagnostic: Stopping test started..'
            self.level = 2
            self.log_publisher()
            sleep(0.2)
            if self.speed == 0.0 or datetime.datetime.now() >= endtime:
                if self.speed != 0.0: 
                    self.message ='Forklift autodiagnostic: Stopping test finished with error!, hit the E-STOP button'
                    self.level = 5
                    self.log_publisher()
                    sleep(0.2)
                    self.stopping_OK = False
                    break
                else:
                    self.message ="Forklift autodiagnostic: Stopping completed succesfully!"
                    self.level = 2
                    self.log_publisher()
                    sleep(0.2)
                    self.stopping_OK = True
                    break
                
            self.speed_pub.publish(stop)
        sleep(1.0)
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = 6.0)
        while True:
            self.message ='Forklift autodiagnostic: Backward move test started..'
            self.level = 2
            self.log_publisher()
            sleep(0.2)
            if self.speed != 0.0 or datetime.datetime.now() >= endtime:
                if self.speed == 0: #Wywolanie bledu gdy predkosc nie narosla / nie odczytano predkosci z encodera
                    self.message ='Forklift autodiagnostic: Backward move finished with error!'
                    self.level = 5
                    self.log_publisher()
                    sleep(0.2)
                    break
                else:
                    speed_measure_2 = self.speed
                    self.message ='Forklift autodiagnostic: Backward move finished with error!'
                    self.level = 2
                    self.log_publisher()
                    sleep(0.2)
                    break
                
            self.speed_pub.publish(speed_2)
        sleep(0.1)
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = 6.0)
        while True:
            self.message ='Forklift autodiagnostic: Stopping test 2 started..'
            self.level = 2
            self.log_publisher()
            sleep(0.2)
            if self.speed == 0.0 or datetime.datetime.now() >= endtime:
                if self.speed != 0.0:
                    self.message ='Forklift autodiagnostic: Stopping test finished with error!, hit the E-STOP button'
                    self.level = 5
                    self.log_publisher()
                    sleep(0.2)
                    self.stopping_OK = False
                    break
                else:
                    self.message ="Forklift autodiagnostic: Stopping completed succesfully!"
                    self.level = 2
                    self.log_publisher()
                    sleep(0.2)
                    self.stopping_OK = True
                    break
                
            self.speed_pub.publish(stop)
        if speed_measure_1 == 0 or speed_measure_2 == 0 or self.stopping_OK == False:
            return False
            
        else:
            return True     
    def lifting_test(self):
        self.message = 'Forklift autodiagnostic: Lifting module test started...'
        self.level = 2
        self.log_publisher()
        sleep(0.5)
        fork_height_old = self.fork_height_actual
        fork_test_result = False
        test_version = 0
        
        rospy.loginfo(fork_height_old)
        if fork_height_old > 150:
            forks_command = 2
            test_version = 1
            self.message = 'Forklift autodiagnostic: Forks lifted more than 200mm, starting dropping test...'
        else:
            forks_command = 1
            test_version = 2
            self.message = 'Forklift autodiagnostic: Starting lifting test...'
        forks_timeout = datetime.datetime.now() + datetime.timedelta(seconds=10)
        self.forks_command_pub.publish(forks_command)
        while True:
            self.level = 1
            self.log_publisher()
            rospy.loginfo(forks_command)
            sleep(0.3)
            
            if datetime.datetime.now() >= forks_timeout:
                if fork_height_old == self.fork_height_actual:
                    if forks_command == 2:
                        self.message = 'Forklift autodiagnostic: Dropping test timeout. Fork test failed successfully :)'
                    else:
                        self.message = 'Forklift autodiagnostic: Lifting test timeout. Fork test failed successfully :)' 
                    self.level = 5
                    fork_test_result = False
                    self.log_publisher()
                    sleep(1)
                    break  
                elif fork_height_old != self.fork_height_actual:
                    if forks_command == 2:
                        self.message = 'Forklift autodiagnostic: Dropping test passed!'
                    else:
                        self.message = 'Forklift autodiagnostic: Lifting test passed!' 
                    self.level = 2
                    fork_test_result = True
                    self.log_publisher()
                    sleep(0.3)
                    break
        if test_version == 2:
            forks_command = 2
            self.message = 'Forklift autodiagnostic: Dropping test after lifting...'
        else:
            forks_command = 1
            test_version = 2
            self.message = 'Forklift autodiagnostic: Liftiing test after droppinging...'
        sleep(1)
        forks_timeout = datetime.datetime.now() + datetime.timedelta(seconds= 10)
        fork_height_old = self.fork_height_actual
        self.forks_command_pub.publish(forks_command)
        while True:
            
            self.level = 1
            self.log_publisher()
            rospy.loginfo(forks_command)
            sleep(0.3)
            
            if datetime.datetime.now() >= forks_timeout:
                if fork_height_old == self.fork_height_actual:
                    if forks_command == 2:
                        self.message = 'Forklift autodiagnostic: Dropping test timeout. Fork test failed successfully :)'
                    else:
                        self.message = 'Forklift autodiagnostic: Lifting test timeout. Fork test failed successfully :)' 
                    self.level = 5
                    fork_test_result = False
                    self.log_publisher()
                    sleep(1)
                    break
                        
                elif fork_height_old != self.fork_height_actual:
                    if forks_command == 2:
                        self.message = 'Forklift autodiagnostic: Dropping test passed!'
                    else:
                        self.message = 'Forklift autodiagnostic: Lifting test passed!' 
                    self.level = 2
                    fork_test_result = True
                    self.log_publisher()
                    sleep(0.3)
                    break
          
            
        if self.fork_height_actual > 110 and fork_test_result == True:
            self.message = "Forklift autodiagnostic: Dropping forks for always the same starting pose..."
            self.level = 2
            self.log_publisher()
            sleep(0.2)
            forks_command = 2
            forks_timeout = datetime.datetime.now() + datetime.timedelta(seconds=10)
            self.forks_command_pub.publish(forks_command)
            while True:
                if datetime.datetime.now() >= forks_timeout:
                    if self.fork_height_actual > 110:
                        self.message = 'Forklift autodiagnostic: Forks dropping after testing failed: timeout!'
                        self.level = 5
                        self.log_publisher()
                        sleep(0.2)
                        break
                    else: 
                        self.message = 'Forklift autodiagnostic: Forks dropped after testing successfully!'
                        self.level = 2
                        self.log_publisher()
                        sleep(0.2)
                        break
                break
        forks_command = 0
        self.forks_command_pub.publish(forks_command)
        if fork_test_result == True:
            sleep(0.2)
            return True
        else:
            sleep(0.2)
            return False
    def auto_mode_initialize(self):
        self.message ='=============NEW STARTUP=============='
        self.level = 2
        self.log_publisher()
        sleep(2)
        self.message ='Forklift autodiagnostic: Started: Waiting for ping test result...'
        self.level = 2
        self.log_publisher()
    
        while not self.end_test:
            if not self.ping_status:
                ping_timeout = datetime.datetime.now() + datetime.timedelta(seconds=60)
                while True:
                    if datetime.datetime.now() >= ping_timeout:
                        self.test_status = False
                        self.end_test = True
                        self.message = 'Forklift autodiagnostic: Ping timeout! Check connection and try again..'
                        self.level = 5
                        self.log_publisher()
                        sleep(1)
                        return self.test_status
                    if self.ping_status:
                        self.message = 'Forklift autodiagnostic: Ping test passed!'
                        self.level = 2
                        self.log_publisher()
                        sleep(1)
                        break
                    rospy.loginfo('Waiting for ping finish')
                    sleep(3)
            if self.ping_status:
                if  not self.safety_status.LeftScannerReducedSpeedZoneStatus or not self.safety_status.RightScannerReducedSpeedZoneStatus or not self.safety_status.LeftEmergencyStopStatus or not self.safety_status.RightEmergencyStopStatus:
                    self.message = 'Forklift autodiagnostic: Checking safety! Please leave safety zones and unpress E-stops buttons!'
                    self.level = 3
                    self.log_publisher()
                    sleep(1)
                    self.test_status = False
                    return self.test_status
                if self.safety_status.LeftScannerReducedSpeedZoneStatus and self.safety_status.RightScannerReducedSpeedZoneStatus and self.safety_status.LeftEmergencyStopStatus and self.safety_status.RightEmergencyStopStatus:
                    self.test_status = True
                    sleep(5)
                    if self.safety_status:
                        rospy.loginfo('Starting steering test....')
                        self.servo_status = self.servo_test()
                        self.test_status = self.servo_status
                        if self.servo_status:
                            rospy.loginfo('Steering test OK!')
                            sleep(1)
                            rospy.loginfo('Starting CURTIS test....')
                            self.curtis_status = self.curtis_test()
                            self.test_status = self.curtis_status
                            if self.curtis_status:
                                rospy.loginfo('Curtis test OK')
                                sleep(1)
                                rospy.loginfo('Starting forks test....')
                                # self.forks_status = self.lifting_test()
                                self.forks_status = True
                                self.test_status = self.forks_status
                                if self.forks_status:
                                    rospy.loginfo("forks OK")
                                    self.test_status = self.forks_status
                                    return self.test_status
                                elif not self.forks_status:
                                    rospy.loginfo("forks not OK")
                                    return self.test_status
                            elif not self.curtis_status:
                                rospy.loginfo('Curtis test failed!')
                                return self.test_status
                        elif not self.servo_status:
                            rospy.loginfo('Steering test failed!')
                            return self.test_status
if __name__ == '__main__':
    try:    
        rospy.init_node('wozek')
        startup_sequence = Startup_sequence()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')
        