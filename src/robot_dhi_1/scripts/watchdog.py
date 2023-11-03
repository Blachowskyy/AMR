#!/usr/bin/env python3
import rospy
import os
import threading
from time import sleep
from std_msgs.msg import String, Int32, Float32

class Watchdog:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.pwm_active = 0.0
        self.pwm_given = 0
        self.pwm_readed = 0
        self.speed_actual = 0.0
        self.angle_setted = 0.0
        self.angle_actual = 0.0
        self.angle_OK = False
        self.speed_OK = False
        self.standstill = True
        self.error_message = ''
        self.error_level = 0
        self.startup_errors = 0
        
        while not rospy.is_shutdown():
            try:
                #Deklaracje subscriberow
                drive_controler_sub1 = rospy.Subscriber('drive_controler_PWM', Int32, self.pwm_active_read, queue_size=1)
                base_controler_sub1 = rospy.Subscriber('comand_curtis_vel', Int32, self.pwm_given_read, queue_size=1)
                drive_controler_sub2 = rospy.Subscriber('drive_controler_PWM_callback', Int32, self.pwm_readed_read, queue_size=1)
                odczyt_encodera_sub1 = rospy.Subscriber('wozek_speed', Int32, self.speed_read, queue_size=1)
                base_controler_sub2 = rospy.Subscriber('comand_servo_angle', Int32, self.angle_setted_read, queue_size=1)
                detectors_sub1 = rospy.Subscriber('servo_angle_tick', Int32, self.angle_actual_read, queue_size=1)
                #Deklaracje publisherow
                self.log_saver_level_pub = rospy.Publisher('logtopic/level', Int32, queue_size=1)
                self.log_saver_message_pub = rospy.Publisher('logtopic/message', String, queue_size=1)
                
            except (rospy.ServiceException, rospy.ROSException) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
            #Start programu glownego
            self.watchdog()
    
    #Odczyty danych z subscriberow
    def pwm_active_read(self, msg):
        self.pwm_active = msg.data     
    def pwm_given_read(self, msg):
        self.pwm_given = msg.data  
    def pwm_readed_read(self, msg):
        self.pwm_readed = msg.data   
    def speed_read(self, msg):
        self.speed_actual = msg.data    
    def angle_setted_read(self, msg):
        self.angle_setted = msg.data    
    def angle_actual_read(self, msg):
        self.angle_actual = msg.data 
    #Sprawdzenie PWM i predkosci   
    def pwm_validation(self):
        #Deklaracja zmiennych lokalnych
        speed_min = 450
        pwm_max = 1200
        pwm_ok = False
        counter = 0
        timeout = 5.0
        #Sprawdzenie, czy jestem w ruchu
        if self.speed_actual != 0:
            in_motion = True
            self.standstill = False
        elif self.speed_actual == 0:
            in_motion = False
            self.standstill = True
        #Jesli nie w ruchu to...
        if in_motion:
            #Jesli wartosc zadana PWM wieksza niz wartosci minimalne
            if self.pwm_given >= speed_min or self.pwm_given <= -speed_min:
                #Zapisz czasu 1
                timer_1 = round(rospy.get_time(), 0)
                #Na start funkcji zapis czasu 2 i zmiana licznika aby ponownie nie trafilo do funkcji zapisu
                if counter == 0:
                    timer_2 = timer_1
                    counter = 1
                #Praca po zmianie licznika
                elif counter != 0:
                    #Jesli roznica czasu wieksza niz timeout
                    if (timer_1 - timer_2) > timeout:
                        #sprawdzenie, czy modul "drive_control.py" zadal PWM.
                        if (self.pwm_active == 0):
                            self.error_level = 5
                            self.error_message = "Drive Control: Vehicle can't stop"
                            self.log_saver_level_pub.publish(self.error_level)
                            self.log_saver_message_pub.publish(self.error_message)
                            self.startup_errors = self.startup_errors + 1
                            pwm_ok = False
                        if (self.pwm_active != 0 and self.pwm_active <= pwm_max):
                            pwm_ok = True
                        #Sprawdzenie komunikacji topicow, czy odczyt zzadanego PWM nie odbiega za bardzo.
                        if ((self.pwm_given - self.pwm_readed) > 200):
                            self.error_level = 3
                            self.error_message = "Topics: Subscriber value different from Publisher"
                            self.log_saver_level_pub.publish(self.error_level)
                            self.log_saver_message_pub.publish(self.error_message)
                        return
        elif not in_motion:
            #Jesli wartosc zadana PWM wieksza niz wartosci minimalne
            if self.pwm_given >= speed_min or self.pwm_given <= -speed_min:
                #Zapisz czasu 1
                timer_1 = round(rospy.get_time(), 0)
                #Na start funkcji zapis czasu 2 i zmiana licznika aby ponownie nie trafilo do funkcji zapisu
                if counter == 0:
                    timer_2 = timer_1
                    counter = 1
                #Praca po zmianie licznika
                elif counter != 0:
                    #Jesli roznica czasu wieksza niz timeout
                    if (timer_1 - timer_2) > timeout:
                        #Jesli pwm aktywne wieksze niz minimalne - blad curtis/PLC
                        if self.pwm_active >= speed_min:
                            self.error_level = 5
                            self.error_message = "Drive_control: PWM given but vehicle is not moving. Check CURTIS!"
                            self.log_saver_level_pub.publish(self.error_level)
                            self.log_saver_message_pub.publish(self.error_message)
                        #Jesli pwm odebrane przez drive_control rowne 0 mimo zadanego - blad komunikacji miedzy programami
                        if self.pwm_readed == 0:
                            self.error_level = 5
                            self.error_message = "Drive_control: Communication with base controller interrupted"
                            self.log_saver_level_pub.publish(self.error_level)
                            self.log_saver_message_pub.publish(self.error_message)
            #Jesli pwm zadane 0 to znaczy, ze wszystko OK
            elif self.pwm_given == 0:
                return
                
                    
        
    def watchdog(self):
        #Uruchamianie programow diagnostycznych jako osbne watki.
        threading.Thread(target=self.pwm_validation).start()
        
if __name__ == '__main__':
    try:    
        rospy.init_node('watchdog')
        watchdog = Watchdog()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')