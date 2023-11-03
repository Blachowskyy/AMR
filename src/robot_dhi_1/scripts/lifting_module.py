#!/usr/bin/env python3

import os
import threading
from time import sleep
import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import Int64, Bool

class lifting_module:

    def __init__(self):

        #Deklaracja zmiennych
        self.mutex = threading.Lock()
        self.cargo = False
        self.load = False
        self.unload = False
        self.tilt_1 = 0
        self.tilt_2 = 0
        self.tilt_1_actual = 0
        self.tilt_2_actual = 0
        self.pressure_read = 0
        self.fork_height = 0
        self.fork_ground_level = 109
        self.work_state = False
        self.lift_up = False
        self.drop_down = False
        self.weight_limit = False
        self.cargo_error = 0
        self.in_motion = False
        self.lifting_modules_status = True

        #Deklaracje subskrybcji i publikacji wiadomosci z systemu ROS
        try:
            self.deltaPLC = ModbusClient(host='192.168.1.4', port=502, auto_open=True, auto_close=True)
            self.work_state_pub = rospy.Publisher('lift_module_work_state', Bool, queue_size=1)
            self.tilt_1_sub = rospy.Subscriber('czujnik_przechylu_w_bok', Int64, self.tilt_1_read)
            self.tilt_2_sub = rospy.Subscriber('czujnik_przechylu_wzdluz', Int64, self.tilt_2_read)
            self.pressure_sub = rospy.Subscriber('czujnik_cisnienia', Int64, self.pressure_reading)
            self.load_command_sub = rospy.Subscriber('forks', Int64, self.fork_callback)
            self.fork_height_sub = rospy.Subscriber('wysokosc_widel', Int64, self.fork_height_read)
            self.in_motion_sub = rospy.Subscriber('motion_status', Bool, self.motion_check)
            rospy.loginfo("Modbus setup complete")
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)
            self.lifting_modules_status = False
            
    def motion_check(self, msg):
        self.in_motion = msg.data

    #Odczyt topicu o wysokosci widel
    def fork_height_read(self, msg):
        self.fork_height = msg.data

    #Odczyt topicu o przechyle w osi 1
    def tilt_1_read(self, msg):
        self.tilt_1_actual = msg.data

    #Odczyt topicu o przechyle w osi 2
    def tilt_2_read(self, msg):
        self.tilt_2_actual = msg.data

    #Odczyt topicu o czujniku cisnienia
    def pressure_reading(self, msg):
        self.pressure_read = msg.data

    def load_command(self):

        tilt_norm = 5 #Norma stopni odchylu od aktualnego polozenia (5 stopni)
        self.tilt_1 = self.tilt_1_actual #Przypisanie aktualnego odchylenia w osi 1
        self.tilt_2 = self.tilt_2_actual #Przypisanie aktualnego odchylenia w osi 2 
        #Ustawienie maksymalnej wartosci odchylenia +/- w obu osiach
        tilt_1_max = self.tilt_1 + tilt_norm
        tilt_1_min = self.tilt_1 - tilt_norm
        tilt_2_max = self.tilt_2 + tilt_norm
        tilt_2_min = self.tilt_2 - tilt_norm
        #Pauza 0.3s 
        sleep(0.3)
        #Wyslanie odpowiedniego polecenia do sterownika PLC o zadaniu
        self.deltaPLC.write_single_register(208, self.loading)
        #Wlaczenie monitora przechylu oraz konca zadania
        monitor = True
        #Petla - monitor przechylu oraz konca akcji
        while monitor == True:
            rospy.loginfo('Monitor sPIN')
            test = False
            #Podczas podnoszenia, gdy wozek ruszy, modul przerwie prace.
            if self.in_motion == True:
                self.deltaPLC.write_single_register(208, 0)
                rospy.loginfo('przerywam - wozek ruszyl')
                self.work_state = False
                monitor = False
            #Monitor przechylu powodujacy wylaczenie aktualnego zadania w przypadku odchylu wiekszego niz zadeklarowana norma
            if self.tilt_1_actual > tilt_1_max or self.tilt_1_actual < tilt_1_min or self.tilt_2_actual > tilt_2_max or self.tilt_2_actual < tilt_2_min:
                self.deltaPLC.write_single_register (208, 0)
                sleep (0.5)
                monitor = False
                self.work_state = False
                rospy.loginfo('Monitor tilt warning')
            #Monitor zakonczenia podnoszenia
            # sleep(5)
            if self.loading == 1 :
                rospy.loginfo('Monitor lifting check')
                limiter = self.deltaPLC.read_holding_registers(209,1)
                self.deltaPLC.write_single_register(208, self.loading)
                rospy.loginfo(limiter)
                if limiter[0] == 1:
                    rospy.loginfo('tu')
                    #Po osiagnieciu limitu wysokosci (1) wlaczenie sprawdzenia czy mam ladunek
                    #oraz sprawdzenie czy nie przekracza maksymalnej ladownosci
                    self.deltaPLC.write_single_register(208, 0)
                    rospy.loginfo(self.pressure_read)
                    if self.pressure_read < 1:
                        self.cargo = False
                        self.weight_limit = False
                        self.cargo_error = 1
                        rospy.loginfo('Monitor lifting check e1')
                        monitor = False
                    if self.pressure_read > 1:
                        self.cargo = True
                        self.weight_limit = False
                        self.cargo_error = 0
                        rospy.loginfo('Monitor lifting check e2')
                        monitor = False
                    if self.pressure_read > 1500:
                        self.cargo = True
                        self.weight_limit = True
                        self.cargo_error = 2
                        rospy.loginfo('Monitor lifting check e3')
                        monitor = False

                #Wyjscie z petli monitorujacej po zakonczeniu zadania.
            #Monitor sprawdzajacy zakonczenie zadania opuszczania
            if self.loading == 2:
                self.deltaPLC.write_single_register(208, self.loading)
                rospy.loginfo('Monitor dropping check')
                rospy.loginfo(self.fork_height)
                # sleep (5)
                #Sprawdzenie czy ladunek odlozony gdy widly osiagna poziom 0
                if self.fork_height <= self.fork_ground_level:
                    self.deltaPLC.write_single_register(208, 0)
                    if self.pressure_read > 150:
                        self.cargo_error = 3
                        rospy.loginfo('error with dropping down pallet')
                        self.lifting_modules_status = False
                        monitor = False
                    elif self.pressure_read < 50:
                        self.cargo_error = 0
                        self.cargo = False
                        rospy.loginfo("cargo dropped")
                        self.lifting_modules_status = False
                        monitor = False
                #Zakonczenie monitora
                # monitor = False
        #Zwolnienie modulu podnoszenia i gotowosc na nastepne zadanie
        self.work_state = False
        rospy.loginfo('Monitor exit')
                

                
    #Program odczytujcy polecenie o podniesieniu (1), opuszczeniu (2) oraz przerwaniu pracy (0)
    def fork_callback(self, msg):
        
        try:
            self.mutex.acquire(blocking=True)
            self.loading = msg.data

            #Zabezpieczenie przed podwojna praca
            if self.work_state == False and self.in_motion == False:
                self.work_state = True
                self.load_command()
                # sleep(5) # pauza 5s pomiedzy zadaniami
            #Sprawdzenie czy zadanie zostalo wykonane
            elif self.in_motion == True:
                self.work_state = False
                rospy.loginfo('Blad - wozek w ruchu')
                self.lifting_modules_status = False
            elif self.work_state != False:
                rospy.logerr("Forks failed")
                self.lifting_modules_status = False
                self.work_state == False
            else:
                rospy.logerr("Forks successfully")
                self.work_state = False

            self.mutex.release()
            
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("fork calback call failed: %s" % e)
            return False
        
    
        
    

if __name__ == '__main__':
    try:
        rospy.init_node('lifting', anonymous=True)
        lifting = lifting_module()
        lifting_module_status_pub = rospy.Publisher('lifting/status', Bool, queue_size=1)
        lifting_module_status_pub.publish(lifting.lifting_modules_status)
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Lifting_module error: %s" % e)
    finally:
        rospy.loginfo('exit')
