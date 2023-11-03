#!/usr/bin/env python3

import os
from pickle import TRUE
from queue import Empty
import threading
from time import sleep
import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import Bool, String, Int64MultiArray
class scangrids_module:

    def __init__(self):

        #Deklaracja zmiennych ogolnych
        self.mutex = threading.Lock()
        self.rate = rospy.Rate(3) # 3Hz
        self.scangrid_reading = []
        self.scangrid_pub = ""
        self.scangrid_state_active = True

        #Deklaracja zmiennych do skanowania odlegości

        self.scangrid_ranges = Int64MultiArray()
        self.scangrid_measure = Int64MultiArray()
        self.scangrid_ranges_boolean = []
        self.bussy = False
        

        #Deklaracja zmiennych - scangrid lewy status
        self.scangrid2L_reading = [] 
        self.scangrid2L_reading_temp = []
        self.scangrid2L_reading_int = []
        self.scangrid2L_reading_bool = []
        self.scangrid2L_working_condition = False
        self.scangrid2L_protective_field_status = False
        self.scangrid2L_interlock = False
        self.scangrid2L_sleep_mode = False
        self.scangrid2L_light_resistance = False
        self.scangrid2L_voltage = False
        self.scangrid2L_CAN_state = False
        self.scangrid2L_monitoring_switch_state = False
        self.scangrid2L_contamination_error = False
        self.scangrid2L_contamination_warning = False
        self.scangrid2L_warning_field_status = False

        #Deklaracja zmiennych - scangrid prawy status

        self.scangrid2R_reading = []
        self.scangrid2R_reading_temp = []
        self.scangrid2R_reading_int = []
        self.scangrid2R_reading_bool = []
        self.scangrid2R_working_condition = False
        self.scangrid2R_protective_field_status = False
        self.scangrid2R_interlock = False
        self.scangrid2R_sleep_mode = False
        self.scangrid2R_light_resistance = False
        self.scangrid2R_voltage = False
        self.scangrid2R_CAN_state = False
        self.scangrid2R_monitoring_switch_state = False
        self.scangrid2R_contamination_error = False
        self.scangrid2R_contamination_warning = False
        self.scangrid2R_warning_field_status = False

        #Deklaracje subskrybcji i publikacji wiadomosci z systemu ROS
        try:
            #Deklaracja i połaczeenie ze sterownikiem PLC
            self.deltaPLC = ModbusClient(host='192.168.1.4', port=502, auto_open=True, auto_close=True)
            #Deklaracja publikowanych topicow
            self.scangrid_state_pub = rospy.Publisher('scangrid_state', String, queue_size=1) # Stan skanerów
            self.autostart_pub = rospy.Publisher('scangrid_state_active', Bool, queue_size=1) # autostart stanu skanerow
            self.scangrid_measure_pub = rospy.Publisher('scangrid_measure', Int64MultiArray, queue_size=10)       
            #Deklaracja nasluchiwanych topicow
            self.scangrid_state_activate_sub = rospy.Subscriber('scangrid_state_active', Bool, self.scangrid_state) # autostart stanu skanerów
            self.scangrid_scan_activate_sub = rospy.Subscriber('scangrid_scan_area', Int64MultiArray, self.scan_callback) # wlaczanie stref monitorowania 
            #Autostart odczytu stanu urzadzen
            self.scangrid_state_callback()         
            rospy.loginfo("Modbus setup complete")
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)

    def scangrid_state_callback(self):
        while not rospy.is_shutdown():
            active = True
            self.autostart_pub.publish(active)
            self.rate.sleep()
            # clear = lambda: os.system('clear')
            # clear()

    def scangrid_state(self, msg):
        self.scangrid_state_active = msg.data
        
        if (self.scangrid_state_active == True and self.bussy == False):
            try:
                rospy.loginfo('')
                #Odczyt rejestrow sterownika PLC
                self.scangrid_reading = self.deltaPLC.read_holding_registers(632, 2)

                #Podizal odczytanych rejestrow miedzy odpowiednie skanery
                self.scangrid2R_reading_temp = bin(self.scangrid_reading[0])
                self.scangrid2L_reading_temp = bin(self.scangrid_reading[1])
                self.scangrid2R_reading = self.scangrid2R_reading_temp[2:]
                self.scangrid2L_reading = self.scangrid2L_reading_temp[2:]
                #Zabezpieczenie pomijania pierwszych liczb zerowych
                if (int(len(self.scangrid2R_reading)) < 16):
                    count = 16 - int(len(self.scangrid2R_reading))
                    for i in range(0, count):
                        self.scangrid2R_reading = "0" + self.scangrid2R_reading
                        i += 1
                if (int(len(self.scangrid2L_reading)) < 16):
                    count = 16 - int(len(self.scangrid2L_reading))
                    for i in range(0, count):
                        self.scangrid2L_reading = "0" + self.scangrid2L_reading
                        i += 1

                #Przypisanie danych z prawego skanera
                self.scangrid2R_working_condition = bool(int(self.scangrid2R_reading[5]))
                self.scangrid2R_protective_field_status = bool(int(self.scangrid2R_reading[6]))
                self.scangrid2R_interlock = bool(int(self.scangrid2R_reading[7]))
                self.scangrid2R_sleep_mode = bool(int(self.scangrid2R_reading[8]))
                self.scangrid2R_light_resistance = bool(int(self.scangrid2R_reading[9]))
                self.scangrid2R_voltage = bool(int(self.scangrid2R_reading[10]))
                self.scangrid2R_CAN_state = bool(int(self.scangrid2R_reading[11]))
                self.scangrid2R_monitoring_switch_state = bool(int(self.scangrid2R_reading[12]))
                self.scangrid2R_contamination_error = bool(int(self.scangrid2R_reading[13]))
                self.scangrid2R_contamination_warning = bool(int(self.scangrid2R_reading[14]))
                self.scangrid2R_warning_field_status = bool(int(self.scangrid2R_reading[15]))

                scangrid2R_info = f'\n Status pola ostrzegawczego: {self.scangrid2R_warning_field_status}, \n Ostrzezenie o zabrudzeniu: {self.scangrid2R_contamination_warning}, \n Blad zabrudzenia: {self.scangrid2R_contamination_error}, \n Blad przelaczania przypadkow monitorowania: {self.scangrid2R_monitoring_switch_state}, \n Blad CAN: {self.scangrid2R_CAN_state}, \n Blad zasilania: {self.scangrid2R_voltage}, \n Blad swiatla zewnetrzne: {self.scangrid2R_light_resistance}, \n Tryb uspienia: {self.scangrid2R_sleep_mode}, \n Interlock: {self.scangrid2R_interlock}, \n Status pola ochronnego: {self.scangrid2R_protective_field_status}, \n Status stanu roboczego: {self.scangrid2R_working_condition}'
                rospy.loginfo('>>>>>>>>>>>>>>>>>>>> \nScangrid Prawy:')
                rospy.loginfo(scangrid2R_info)

                #Przypisanie danych z lewego skanera
                self.scangrid2L_working_condition = bool(int(self.scangrid2L_reading[5]))
                self.scangrid2L_protective_field_status = bool(int(self.scangrid2L_reading[6]))
                self.scangrid2L_interlock = bool(int(self.scangrid2L_reading[7]))
                self.scangrid2L_sleep_mode = bool(int(self.scangrid2L_reading[8]))
                self.scangrid2L_voltage = bool(int(self.scangrid2L_reading[10]))
                self.scangrid2L_CAN_state = bool(int(self.scangrid2L_reading[11]))
                self.scangrid2L_monitoring_switch_state = bool(int(self.scangrid2L_reading[12]))
                self.scangrid2L_contamination_error = bool(int(self.scangrid2L_reading[13]))
                self.scangrid2L_contamination_warning = bool(int(self.scangrid2L_reading[14]))
                self.scangrid2L_warning_field_status = bool(int(self.scangrid2L_reading[15]))

                scangrid2L_info = f'\n Status pola ostrzegawczego: {self.scangrid2L_warning_field_status}, \n Ostrzezenie o zabrudzeniu: {self.scangrid2L_contamination_warning}, \n Blad zabrudzenia: {self.scangrid2L_contamination_error}, \n Blad przelaczania przypadkow monitorowania: {self.scangrid2L_monitoring_switch_state}, \n Blad CAN: {self.scangrid2L_CAN_state}, \n Blad zasilania: {self.scangrid2L_voltage}, \n Blad swiatla zewnetrzne: {self.scangrid2L_light_resistance}, \n Tryb uspienia: {self.scangrid2L_sleep_mode}, \n Interlock: {self.scangrid2L_interlock}, \n Status pola ochronnego: {self.scangrid2L_protective_field_status}, \n Status stanu roboczego: {self.scangrid2L_working_condition}'
                rospy.loginfo('>>>>>>>>>>>>>>>>>>>> \nScangrid Lewy:')
                rospy.loginfo(scangrid2L_info)

                self.scangrid_pub = self.scangrid2R_reading + "," + self.scangrid2L_reading
                self.scangrid_state_pub.publish(self.scangrid_pub)
                rospy.loginfo("Message pubished")
            except:
                rospy.logerr("fork calback call failed: %s" % e)
                return False

    def measure(self):

        try:
            self.bussy = True
            tmp = []
            tmp1 = []
            self.mutex.acquire()
            self.deltaPLC.write_multiple_coils(41120, self.scangrid_ranges_boolean)
            tmp = self.deltaPLC.read_holding_registers(600, 32)
            tmp1 = self.deltaPLC.read_holding_registers(700, 32)
            tmp = tmp1 + tmp
            self.mutex.release()
            self.scangrid_measure.data = tmp
            rospy.loginfo(tmp)
            self.scangrid_measure_pub.publish(self.scangrid_measure)
            self.bussy = False
            sleep (1)
        except:
            rospy.logerr("fork calback call failed: %s" % e)
            return False   
                   
    def measure_reset(self):
        self.scangrid_ranges_boolean.clear
        for i in range (1, 65):
            self.scangrid_ranges_boolean.append(False)
            i += 1
        self.deltaPLC.write_multiple_coils(41120, self.scangrid_ranges_boolean)
        rospy.loginfo('Turned off measuring')

    def scan_callback(self, msg):

        try:
            self.scangrid_ranges = msg.data #Tablica którą otrzymujemy - liczby 1 - 64 np. [1, 5, 12]
            self.scangrid_ranges_boolean.clear()
            b = 0
            for i in range (1, 65):
                if ( b < int(len(self.scangrid_ranges))):
                    if (self.scangrid_ranges[b] == i):
                        self.scangrid_ranges_boolean.append(True)
                        b += 1
                        rospy.loginfo(b)
                    elif (self.scangrid_ranges[b] != i):
                        self.scangrid_ranges_boolean.append(False)
                else:
                     self.scangrid_ranges_boolean.append(False)
            
            rospy.loginfo(self.scangrid_ranges_boolean)
            rospy.loginfo(len(self.scangrid_ranges_boolean))
            self.measure() # włączenie zapisu listy sygnałów do PLC
            self.rate.sleep()
            sleep(20)  
            self.measure_reset()

        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("fork calback call failed: %s" % e)
            return False
        
if __name__ == '__main__':
    try:
        rospy.init_node('scangrids', anonymous=True)
        scangrids = scangrids_module()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
        
    except rospy.ROSInterruptException as e:
        rospy.logerr("Lifting_module error: %s" % e)
    finally:
        rospy.loginfo('exit')
