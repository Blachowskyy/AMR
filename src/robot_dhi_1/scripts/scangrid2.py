#!/usr/bin/env python3
import os
import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import Int64MultiArray

def publisher():

    #Deklaracja topic list wysylanych do ROS
    scangrid2_pub1 = rospy.Publisher('scangrid_1', Int64MultiArray, queue_size=10)
    scangrid2_pub2 = rospy.Publisher('scangrid_2', Int64MultiArray, queue_size=10)
    rospy.init_node('scangrid', anonymous=True)

    #Deklaracja polaczenia modbus
    delta = ModbusClient(host='192.168.1.4',port=502,auto_open=True, auto_close=True)
    rate = rospy.Rate(3) # 1hz
    rospy.loginfo("Publisher high started")
    scangrid1 = Int64MultiArray()
    scangrid2 = Int64MultiArray()
    scangrid_activate_values = False


    while not rospy.is_shutdown():
        
        if (scangrid_activate_values == True):
            scangrid1.data = delta.read_holding_registers(600, 32)
            scangrid2.data = delta.read_holding_registers(700, 32)

            #Wyswietlenie w konsoli
            rospy.loginfo("Scangrid data active")

            #Publikowanie wybranych informacji jako topic ROS
            scangrid2_pub1.publish(scangrid1)
            scangrid2_pub2.publish(scangrid2)
            rate.sleep()
            clear = lambda: os.system('clear')
            clear()
        rospy.loginfo('tu')
     
        #odczyt ze sterownika PLC
        scangrid_state = delta.read_holding_registers(632, 2)
        scangrid_1_state = scangrid_state[0]
        scangrid_2_state = scangrid_state[1]

        #konwersja 16 it na wartosci binarne ( lista )
        scangrid_1_byte_state_tmp = bin(scangrid_1_state)
        scangrid_1_byte_state = scangrid_1_byte_state_tmp[2:]
        scangrid_2_byte_state_tmp = bin(scangrid_2_state)
        scangrid_2_byte_state = scangrid_2_byte_state_tmp[2:]

        #Gdy bity zaczynaja sie od 0, to sa pomijane. Funkcja dopisuje brakujace 0 dla obu skanerow
        if (int(len(scangrid_1_byte_state) < 16)):
            temp1 = 16 - len(scangrid_1_byte_state)
            for i in range (0, temp1):
                scangrid_1_byte_state = "0" + scangrid_1_byte_state
                i = i + 1

        if (int(len(scangrid_2_byte_state) < 16)):
            temp2 = 16 - len(scangrid_2_byte_state)
            for i in range (0, temp2):
                scangrid_2_byte_state = "0" + scangrid_2_byte_state
                i = i + 1
        rospy.loginfo(scangrid_1_byte_state)
        rospy.loginfo(scangrid_2_byte_state)
        #State of scangrid2 left 
        scangrid2L_working_condition = bool(int(scangrid_1_byte_state[5]))
        scangrid2L_protective_field_status = bool(int(scangrid_1_byte_state[6]))
        scangrid2L_interlock = bool(int(scangrid_1_byte_state[7]))
        scangrid2L_sleep_mode = bool(int(scangrid_1_byte_state[8]))
        scangrid2L_light_resistance = bool(int(scangrid_1_byte_state[9]))
        scangrid2L_voltage = bool(int(scangrid_1_byte_state[10]))
        scangrid2L_CAN_state = bool(int(scangrid_1_byte_state[11]))
        scangrid2L_monitoring_switch_state = bool(int(scangrid_1_byte_state[12]))
        scangrid2L_contamination_error = bool(int(scangrid_1_byte_state[13]))
        scangrid2L_contamination_warning = bool(int(scangrid_1_byte_state[14]))
        scangrid2L_warning_field_status = bool(int(scangrid_1_byte_state[15]))

        scangrid2L_info = f'\n Status pola ostrzegawczego: {scangrid2L_warning_field_status}, \n Ostrzezenie o zabrudzeniu: {scangrid2L_contamination_warning}, \n Blad zabrudzenia: {scangrid2L_contamination_error}, \n Blad przelaczania przypadkow monitorowania: {scangrid2L_monitoring_switch_state}, \n Blad CAN: {scangrid2L_CAN_state}, \n Blad zasilania: {scangrid2L_voltage}, \n Blad swiatla zewnetrzne: {scangrid2L_light_resistance}, \n Tryb uspienia: {scangrid2L_sleep_mode}, \n Interlock: {scangrid2L_interlock}, \n Status pola ochronnego: {scangrid2L_protective_field_status}, \n Status stanu roboczego: {scangrid2L_working_condition}'
        rospy.loginfo('SCANGRID LEWY')
        rospy.loginfo(scangrid2L_info)
    
        #State of scangrid2 right 
        scangrid2R_working_condition = bool(int(scangrid_2_byte_state[5]))
        scangrid2R_protective_field_status = bool(int(scangrid_2_byte_state[6]))
        scangrid2R_interlock = bool(int(scangrid_2_byte_state[7]))
        scangrid2R_sleep_mode = bool(int(scangrid_2_byte_state[8]))
        scangrid2R_light_resistance = bool(int(scangrid_2_byte_state[9]))
        scangrid2R_voltage = bool(int(scangrid_2_byte_state[10]))
        scangrid2R_CAN_state = bool(int(scangrid_2_byte_state[11]))
        scangrid2R_monitoring_switch_state = bool(int(scangrid_2_byte_state[12]))
        scangrid2R_contamination_error = bool(int(scangrid_2_byte_state[13]))
        scangrid2R_contamination_warning = bool(int(scangrid_2_byte_state[14]))
        scangrid2R_warning_field_status = bool(int(scangrid_2_byte_state[15]))
        rospy.loginfo(scangrid_1_byte_state[6])
        rospy.loginfo(scangrid_2_byte_state[6])

        scangrid2R_info = f'\n Status pola ostrzegawczego: {scangrid2R_warning_field_status}, \n Ostrzezenie o zabrudzeniu: {scangrid2R_contamination_warning}, \n Blad zabrudzenia: {scangrid2R_contamination_error}, \n Blad przelaczania przypadkow monitorowania: {scangrid2R_monitoring_switch_state}, \n Blad CAN: {scangrid2R_CAN_state}, \n Blad zasilania: {scangrid2R_voltage}, \n Blad swiatla zewnetrzne: {scangrid2R_light_resistance}, \n Tryb uspienia: {scangrid2R_sleep_mode}, \n Interlock: {scangrid2R_interlock}, \n Status pola ochronnego: {scangrid2R_protective_field_status}, \n Status stanu roboczego: {scangrid2R_working_condition}'
        rospy.loginfo('SCANGRID PRAWY')
        rospy.loginfo(scangrid2R_info)

        # scangrid2R_pub_state.publish(scangrid_2_string_state)
        rate.sleep()
        clear = lambda: os.system('clear')
        clear()

if __name__ == '__main__':
    try:
        publisher()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)