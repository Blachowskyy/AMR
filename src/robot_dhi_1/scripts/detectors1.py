#!/usr/bin/env python3
import os
import rospy
from pyModbusTCP.client import ModbusClient
from std_msgs.msg import Int64, Bool, Float32
from nav_msgs.msg import Odometry


# global wozek_uzyto_raczki
# global c

# def confirmLocalized(msg):
#     if(wozek_uzyto_raczki == False):
#         rospy.loginfo("Otrzymalem wiadomosc od odometrii")
#         # wysylanie do PLCka 
#         localized = True
#         # TO DO: wpisac nr rejestru 
#         c.write_single_register( ,localized)



def publisher():
    detectors_status = True
    
    #Deklaracja topic list wysylanych do ROS
    pub = rospy.Publisher('wysokosc_widel', Int64, queue_size=1)
    pub2 = rospy.Publisher('czujnik_cisnienia', Int64, queue_size=10)
    pub3 = rospy.Publisher('czujnik_przechylu_w_bok', Int64, queue_size=10)
    pub4 = rospy.Publisher('czujnik_przechylu_wzdluz', Int64, queue_size=10)

    servo_kierunek_pub = rospy.Publisher('servo_active_direction', Int64, queue_size=10)
    servo_error_pub = rospy.Publisher('servo_is_error', Bool, queue_size=10)
    servo_blad_pub = rospy.Publisher('servo_error_code', Int64, queue_size=10)
    servo_pozycja_pub = rospy.Publisher('servo_angle_tick', Float32, queue_size=100)
    servo_event_pub = rospy.Publisher('servo_active_event', Int64, queue_size=10)
    manual_mode_pub = rospy.Publisher('manual_jog', Int64, queue_size=10)

    
    # publisher , ze uzyto raczki 
    # handle_used_pub = rospy.Publisher('handle_used_event', Bool, queue_size=10)

    rospy.init_node('detectors', anonymous=True)
    detectors_status_pub = rospy.Publisher('detectors/status', Bool, queue_size=1)
    # rospy.Subscriber('odom',Odometry,confirmLocalized)
    # rospy.spin()

    #Deklaracja polaczenia modbus
    c=ModbusClient(host='192.168.1.4',port=502,auto_open=True, auto_close=True)
    rate = rospy.Rate(10) # 1hz
    rospy.loginfo("Publisher high started")
    while not rospy.is_shutdown():
        offset = 180
        read0 = c.read_holding_registers(200, 5)
        read1 = c.read_holding_registers(211, 5)
        read2 = c.read_coils(41040, 2)

        #Odczyt z PLC ( analog )
        #read_holding_registers(adres_rejestru, ilosc_rejestrow)
        widly_level = read0[0]
        wozek_pressure = read0[1]
        wozek_na_boki_detector = read0[3]
        wozek_wzdluz_detector = read0[2]
        wozek_battery_lewel_temp = read0[4]
        #Odczyt z PLC diagnostyka

        error_analog = read2[0]
        error_can = read2[1]
        error_analog_id_code = c.read_holding_registers(300, 2)
        error_id_code = c.read_holding_registers(303, 2)
 

        #Odczyt z PLC ( wejscia cyfrowe )
        #read_coils(adres, ilosc_bitow_do_odc)
        #czym sie rozni discrete inputs od coils?
        # wozek_interlock = c.read_discrete_inputs(24576, 1)
        # wozek_beacon_status = c.read_coils(24577, 1)
        # wozek_reverse_sound = c.read_coils(24578, 1)
        # wozek_uzyto_raczki = c.read_coils(24669, 1)
        
        #Odczyt z PLC stan serwonapedu
        manual_jog_used = read1[4]
        servo_kierunek = read1[0]
        servo_pozycja_tmp = read1[1]
        servo_error = False
        servo_blad = read1[2]
        servo_event = read1[3]
       

        #Logika
        # POZIOM BATERII
        wozek_battery_lewel = wozek_battery_lewel_temp / 100
        battery_percentage = 100 - ((28.0 - wozek_battery_lewel) / 0.0743)
        battery_percentage = round(battery_percentage, 0)
        if battery_percentage >= 100:
            battery_percentage = 100
        if battery_percentage <= 15:
            battery_low = True
            rospy.loginfo("POTRZEBNE LADOWANIE, NISKI STAN BATERI")
        elif battery_percentage > 15:
            battery_low = False
            rospy.loginfo("Stan bateri: OK")
        
        #SPRAWDZANIE CZY JEST PROBLEM Z SERWEM 
        if servo_blad == 0:
            servo_error = False
        else:
            servo_error = True
            detectors_status = False
        
        servo_pozycja_tmp2 = servo_pozycja_tmp / 100
        if servo_kierunek == 1:
            servo_pozycja = servo_pozycja_tmp2 * -1
        elif servo_kierunek == 2:
            servo_pozycja = servo_pozycja_tmp2 * 1 
        else:
            rospy.loginfo("Blad kierunku!")
        
        # WYSYLANIE SYGNALU POTWIERDZENIA, ZE ROS WIE GDZIE WOZEK JEST

        #Deklaracja informacji wyswietlanych w konsoli
        detectors_info= f"\nAktualna wysokosc widel: {widly_level}mm,\nWaga na widlach: {wozek_pressure} kg,\nCzujnik przechylu w bok: {wozek_na_boki_detector - offset} stopni,\nCzujni przechylu wzdluz: {wozek_wzdluz_detector - offset} stopni,\nNapiecie baterii {wozek_battery_lewel}V, \nProcent baterii: {battery_percentage}%"
        wozek_status = f"\nStan baterii krytyczny: {battery_low}, \nUzyto trybu recznego: {manual_jog_used}"
        diagnostic_status = f"\n Blad wyjsc/wejsc analogowych: {error_analog},\nBlad w module analog: {error_analog_id_code[0]},\nKod bledu analog: {error_analog_id_code[1]}\nBlad komunikacji CAN: {error_can},\nBlad w module CAN: {error_id_code[0]},\nKod bledu: {error_id_code[1]}"
        servo_status = f"\nZadany kierunek: {servo_kierunek}, \nAktualny kat servonapedu: {servo_pozycja}, \nBlad serwonapedu: {servo_error}, \nKod bledu serwonapedu: {servo_blad}, \nAktualny event serwonapedu: {servo_event}"
        #Wyswietlenie w konsoli
        rospy.loginfo(detectors_info)
        rospy.loginfo(wozek_status)
        rospy.loginfo(diagnostic_status)
        rospy.loginfo(servo_status)

        #Publikowanie wybranych informacji jako topic ROS
        pub4.publish(wozek_wzdluz_detector - offset)
        pub3.publish(wozek_na_boki_detector - offset)
        pub2.publish(wozek_pressure)
        pub.publish(widly_level)

        # handle_used_pub.publish(wozek_uzyto_raczki)


        manual_mode_pub.publish(manual_jog_used)
        servo_pozycja_pub.publish(servo_pozycja)
        rate.sleep()
        # clear = lambda: os.system('clear')
        # clear()


if __name__ == '__main__':
    try:
        publisher()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Encoder error: %s" % e)
