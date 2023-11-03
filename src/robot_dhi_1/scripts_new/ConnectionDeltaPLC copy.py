#!/usr/bin/env python3

import threading
import os
from time import sleep
from pyModbusTCP import client
import rospy
from std_msgs.msg import Int64, String, Bool, Int32, Int64MultiArray, ByteMultiArray
from robot_dhi_1.msg import DistanceDrive as DD
import signal
import asyncio
from async_class import AsyncClass

# Program komunikacyjny ROS <--> PLC
class PLC:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.mutex = threading.Lock()
        self.ROS_write = [0] * 99
        self.ROS_read = [0] * 99
        self.PLC_err_ids = [0] * 10
        self.PLC_virtual_IO = [0] * 10
        self.PLC_signals_IN = [None] * 80
        self.PLC_signals_OUT = [False] * 80
        self.PLC_workstates_IN_temp = []
        self.PLC_signals_IN_old = [False] * 80
        self.PLC_signals_OUT_old = [False] * 80
        self.Forklift_states_read = ByteMultiArray()
        self.Forklift_states_write = ByteMultiArray()
        self.readed_IO = [False] * 80
        self.Scangrid2R = Int64MultiArray()
        self.Scangrid2L = Int64MultiArray()
        self.scangrid_merged = Int64MultiArray()
        
        self.error_list = [0] * 99
        self.pwm_value = 0
        self.pwm_direction = 0
        self.servo_value = 0
        self.servo_direction = 0
        self.servo_off = 0
        self.give_workstate = 1
        self.servo_power = 0
        self.scangrids_activator = False
        self.err_code = 0
        self.log_message = ''
        self.log_level = 0
        self.forks_command = 0
        self.Plc_connection = True
        self.watchdog_now = 1
        self.watchdog_last= 0
        self.operator_reset_auto = False
        self.operator_logged_in = False
        self.rate = rospy.Rate(10) # 10Hz
        self.clear = lambda: os.system('clear')
        self.delta_PLC = client.ModbusClient("192.168.1.4", 502, auto_close=True, auto_open=True)
        self.Plc_connect()
        # for i in range (0,8):
        #     self.Forklift_states_write.data.append(False)
        while not rospy.is_shutdown():
            try:
                
                #Deklaracje publikowanych i odczytywanych topicow ROS ( publikujemy dane PLC, odczytujemy dane do zapisu w PLC)
                
                self.forks_height_pub = rospy.Publisher('PLC/read/fork_height', Int64, queue_size=1)
                self.cargo_weight_pub = rospy.Publisher('PLC/read/cargo_weight', Int64, queue_size=1)
                self.tilt_axis_1_pub = rospy.Publisher('PLC/read/tilt_axis_1', Int64, queue_size=1)
                self.tilt_axis_2_pub = rospy.Publisher('PLC/read/tilt_axis_2', Int64, queue_size=1)
                self.battery_voltage_pub = rospy.Publisher('PLC/read/battery_voltage', Int64, queue_size=1)
                self.encoder_speed_pub = rospy.Publisher('PLC/read/encoder_speed', Int64, queue_size=1)
                self.encoder_direction_pub = rospy.Publisher('PLC/read/encoder_direction', Int64, queue_size=1)
                self.forks_height_limiter_pub = rospy.Publisher('PLC/read/forks_height_limiter', Int64, queue_size=1)
                self.servo_direction_pub = rospy.Publisher('PLC/read/servo_direction', Int64, queue_size=1)
                self.servo_angle_pub = rospy.Publisher('PLC/read/servo_angle', Int64, queue_size=1)
                self.current_work_state_pub = rospy.Publisher('PLC/read/current_work_state', Int64, queue_size=1)
                self.log_message_pub = rospy.Publisher('log/message', String, queue_size=10)
                self.log_level_pub = rospy.Publisher('log/level', Int32, queue_size=10)
                self.scangrid1ranges_pub = rospy.Publisher('PLC/read/scangrid1ranges', Int64MultiArray, queue_size=1)
                self.scangrid2ranges_pub = rospy.Publisher('PLC/read/scangrid2ranges', Int64MultiArray, queue_size=1)
                self.Forklift_states_read_pub = rospy.Publisher('Forklift/state/workstate_actual_list', ByteMultiArray, queue_size=1)
                self.Forklift_reinitialize_auto_pub = rospy.Publisher('Forklift/state/user/reinitialise_auto', Bool, queue_size=1)
                
                #Deklaracje subskrybowanych topicow ROS
                self.Forklift_states_write_sub = rospy.Subscriber('Forklift/state/workstate_requested_list', ByteMultiArray, self.workstate_read)
                self.servo_direction_sub = rospy.Subscriber('PLC/write/servo_direction', Int64, self.servo_direction_read)
                self.servo_value_sub = rospy.Subscriber('PLC/write/servo_value', Int64, self.servo_value_read)
                self.user_logged_sub = rospy.Subscriber('Forklift/state/user/login_status', Bool, self.user_login_read)
                self.PWM_sub = rospy.Subscriber('PLC/write/command_pwm_value', Int64, self.command_pwm_read)
                self.PWM_dir_sub = rospy.Subscriber('PLC/write/command_pwm_direction', Int64, self.command_pwm_direction)
                self.servo_power_sub = rospy.Subscriber('PLC/write/servo_power', Int64, self.servo_power_read)
                # self.scangrid_activation_sub = rospy.Subscriber('PLC/write/scangrids_activate', Bool, self.scangrids_activation_read)
                self.forks_command_sub = rospy.Subscriber('PLC/write/forks_command', Int64, self.forks_command_read)
                
            except(rospy.ServiceException, rospy.ROSException, SystemExit) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
            #Wyzwolenie komunikacji
            self.Communication()
    
    def user_login_read(self, msg):
        self.operator_logged_in = msg.data          
    def command_pwm_read(self, msg):
        #Odczyt zadanej wartosci PWM do napedu wozka
        self.pwm_value = msg.data
    def command_pwm_direction(self, msg):
        #Odczyt zadanego kierunku ruchu do napedu wozka
        self.pwm_direction = msg.data
    def servo_direction_read(self, msg):
        #Odczyt zadanego kierunku skretu (serwonaped)
        self.servo_direction = msg.data
    def servo_value_read(self, msg):
        #Odczyt zadanego kata skretu (serwonaped)
        self.servo_value = msg.data
    def servo_power_read(self, msg):
        #Odczyt zadanego stanu serwonapedu ( ON/OFF )
        self.servo_power = msg.data
    def workstate_read(self, msg):
        #Odczyt zadanego stanu pracy
        self.Forklift_states_write.data = msg.data   
    def ReadList(self):
        #Sortowanie i publikowanie do topicow ROS danych z odczytanej tabeli z PLC
        self.mutex.acquire()
        self.ROS_read = self.delta_PLC.read_holding_registers(200, 99) # Odczyt 99 rejestrow z PLC
        self.mutex.release()
        if self.ROS_read != None:
            self.forks_height_pub.publish(self.ROS_read[0])
            self.cargo_weight_pub.publish(self.ROS_read[1])
            self.tilt_axis_1_pub.publish(self.ROS_read[2])
            self.tilt_axis_2_pub.publish(self.ROS_read[3])
            self.battery_voltage_pub.publish(self.ROS_read[4])
            self.encoder_speed_pub.publish(self.ROS_read[5])
            self.encoder_direction_pub.publish(self.ROS_read[6])
            self.forks_height_limiter_pub.publish(self.ROS_read[7])
            self.servo_direction_pub.publish(self.ROS_read[8])
            self.servo_angle_pub.publish(self.ROS_read[9])
            self.current_work_state_pub.publish(self.ROS_read[10])
            return True
        else:
            self.Plc_connection = False
            return False
    def WriteList(self):
        #Sortowanie i zapisywanie danych otrzymanych do zapisu do PLC w liste
        self.ROS_write[0] = self.servo_direction
        self.ROS_write[1] = self.servo_value
        self.ROS_write[2] = self.servo_power
        self.ROS_write[3] = self.give_workstate 
        self.ROS_write[4] = self.pwm_direction 
        self.ROS_write[5] = self.pwm_value
        self.ROS_write[6] = self.forks_command
        self.ROS_write[98] = self.watchdog_now
    def IO_Write(self):
        self.PLC_signals_IN[0] = self.scangrids_activator
        #Petla przekazania stanow pracy na liste zapisu do PLC
        rospy.loginfo(self.Forklift_states_write)
        if self.Forklift_states_write.data != None:
            j = 0
            offset = 8
            tmp = len(self.Forklift_states_write.data) + offset
            for i in range(offset, tmp ):
                self.PLC_signals_IN[i] = bool(self.Forklift_states_write.data[j])
                j = j + 1
        self.PLC_signals_IN[24] = self.operator_logged_in
        for i in range (0, len(self.PLC_signals_IN)):
            if self.PLC_signals_IN[i] == None:
                self.PLC_signals_IN[i] = False
        
        rospy.loginfo (self.PLC_signals_IN)
        self.delta_PLC.write_multiple_coils(41120, self.PLC_signals_IN) # Zapis sygnalow w PLC ( limit 80 )
        rospy.loginfo('Data_change_write')

        
        rospy.loginfo('IO_WRITE_LOOP')
    def IO_Read(self):
        self.PLC_signals_OUT = self.delta_PLC.read_coils(41200, 80)
        if self.PLC_signals_OUT != None:
            rospy.loginfo (self.PLC_signals_OUT)
            for i in range (8, 24):
                self.Forklift_states_read.data.append(self.PLC_signals_OUT[i])
            self.Forklift_states_read_pub.publish(self.Forklift_states_read)
            self.Forklift_reinitialize_auto_pub.publish(self.operator_reset_auto)
            self.operator_reset_auto = self.PLC_signals_OUT[24]

            self.Forklift_states_read.data.clear()
        else:
            rospy.loginfo('Signals_Out none type')
    def ErrorList(self):
        #Odczyt wewnetrznych bledow w PLC i przekazanie ich w topic log_saver
        module_str = ''
        error_code = ''
        self.error_list = self.delta_PLC.read_holding_registers(500, 99) # Odczyt tablicy kodow bledow
        
        if self.error_list != None and self.Plc_connection:
                #Podczialy bledow na moduly, przypisanie wagi bledu oraz dodanie nazwy modulu i kodu bledu do zapisu
            if self.error_list[0] != 0:
                module_str = 'Scagrid left error code:'
                error_code = str(self.error_list[0])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                if self.give_workstate == 3 :
                    self.log_level = 5
                else:
                    self.log_level = 3
                self.log_level_pub.publish(self.log_level)
            if self.error_list[1] != 0:
                module_str = 'Scagrid right error code:'
                error_code = str(self.error_list[1])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                if self.give_workstate == 3 :
                    self.log_level = 5
                else:
                    self.log_level = 3
                self.log_level_pub.publish(self.log_level)
            if self.error_list[2] != 0:
                module_str = 'Pressure sensor error code:'
                error_code = str(self.error_list[2])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                self.log_level = 4
                self.log_level_pub.publish(self.log_level)
            if self.error_list[3] != 0:
                module_str = 'Forks height sensor error code:'
                error_code = str(self.error_list[3])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                self.log_level = 4
                self.log_level_pub.publish(self.log_level)
            if self.error_list[4] != 0:
                module_str = 'Tilt sensor axis 1 error code:'
                error_code = str(self.error_list[4])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                self.log_level = 4
                self.log_level_pub.publish(self.log_level)
            if self.error_list[5] != 0:
                module_str = 'Tilt sensor axis 2 error code:'
                error_code = str(self.error_list[5])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                self.log_level = 4
                self.log_level_pub.publish(self.log_level)
            if self.error_list[6] != 0:
                module_str = 'Battery read error code:'
                error_code = str(self.error_list[6])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                self.log_level = 5
                self.log_level_pub.publish(self.log_level)
            if self.error_list[8] != 0:
                module_str = 'Curtis speed write error code:'
                error_code = str(self.error_list[8])
                self.log_message = module_str + error_code
                self.log_message_pub.publish(self.log_message)
                self.log_level = 4
                self.log_level_pub.publish(self.log_level)
            else:
                self.log_level = 0
                self.log_message = ''
                error_code = ''
                module_str = ''
        else:
            self.Plc_connection = False
    def Scangrids(self):
        #Odczyt danych otrzymanych z Scangrid2
        
        self.Scangrid2L.data= self.delta_PLC.read_holding_registers(600, 31)
        self.Scangrid2R.data = self.delta_PLC.read_holding_registers(650, 31)
        if self.Scangrid2L == None:
            self.log_message = 'PLC Communication: Error in readings from Scangrid left'
            self.log_level = 4
            self.log_level_pub.publish(self.log_level)
            self.log_message_pub.publish(self.log_message)
            self.Plc_connection = False
        if self.Scangrid2R == None:
            self.log_message = 'PLC Communication: Error in readings from Scangrid right'
            self.log_level = 4
            self.log_level_pub.publish(self.log_level)
            self.Plc_connection = False
            self.log_message_pub.publish(self.log_message)
        self.scangrid1ranges_pub.publish(self.Scangrid2L)
        self.scangrid2ranges_pub.publish(self.Scangrid2R)
    def Plc_connect(self):
        self.delta_PLC.close()
        self.delta_PLC = None
        self.delta_PLC = client.ModbusClient("192.168.1.4", 502, auto_close=True, auto_open=True)
        rospy.loginfo('+++++++++<<<<<< RECONNECTION LOOP >>>>>>++++++++')            
    def watchdog(self):
        self.watchdog_last = self.watchdog_now
        if self.watchdog_last == 1:
            self.watchdog_now = 2
        elif self.watchdog_last == 2:
            self.watchdog_now = 1
    def forks_command_read(self, msg):
        self.forks_command = msg.data
    def Communication(self):
        rospy.loginfo('kurde') 
        self.ReadList() #Wywolanie sortowania odczytanych sygnalow
        self.WriteList() #wywolanie sortowania danych z ROS do zapisu
        self.watchdog()
        self.mutex.acquire()
        info = self.delta_PLC.write_multiple_registers(100, self.ROS_write) # Zapis rejestrow PLC ( limit 99 )
        self.mutex.release()
        if info == None and self.Plc_connection:
            self.log_message = 'PLC Communication: Error in writing PLC Datatable.'
            self.log_level = 5
            self.log_level_pub.publish(self.log_level)
            self.log_message_pub.publish(self.log_message)
            self.Plc_connection = False
        self.IO_Read() #Wywoalnie sortowania sygnalow z ROS do zapisu 
        self.IO_Write()
        if info == None and self.Plc_connection:
            self.log_message = 'PLC Communication: Error in writing IO to PLC.'
            self.log_level = 5
            self.log_level_pub.publish(self.log_level)
            self.log_message_pub.publish(self.log_message)
            self.Plc_connection = False
        if self.error_list != None:
            self.ErrorList()
        self.rate.sleep() #Odswiezanie
        #czyszczenie list
        if self.ROS_read != None:
            self.ROS_read.clear()
        if self.PLC_virtual_IO != None:
            self.PLC_virtual_IO.clear()
        self.clear() 
        #Wywolanie modulow Scangrid gdy aktywowany
        self.Scangrids()
        self.rate.sleep()
        rospy.loginfo('+++++++++<<<<<< COMMUNICATION LOOP >>>>>>++++++++')            

if __name__ == '__main__':
    try:    
        rospy.init_node('plc_communication')
        plc = PLC()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')