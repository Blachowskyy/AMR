#!/usr/bin/env python3
import os
import time
import subprocess
import rospy
from std_msgs.msg import Bool, String, Int32


def check_connection():
    rospy.init_node('ping', anonymous=True) #Inicjacja node'a
    #Pula adresow IP urzadzen, z ktorymi jest polaczenie poprzez ethernet.
    address_PLC = '192.168.1.4' 
    address_FlexiCPU = '192.168.1.11'
    address_Lidarloc = '192.168.1.1'
    address_router = '192.168.1.6'
    address_Scanner_1 = '192.168.1.30'
    address_Scanner_2 = '192.168.1.32'
    #Deklaracje pozostalych zmiennych  
    ping_status = False
    start = True
    responce_all = 1 #Tu dodaja sie wszystkie odpowiedzi urzadzen ( 0 - OK, liczba - blad)
    message = '' #Tu dodaja sie statusy zapisywane w logu
    retry_counter = 0 #Licznik powtorzen pingowania w przypadku braku lacznosci za 1 proba
    #Deklaracje publisherow
    ping_status_pub = rospy.Publisher('Forklift/state/startup/ping_status', Bool, queue_size=1, latch=True) #Publisher topic'u zawierajacego status proby pingowania
    message_pub = rospy.Publisher('logtopic/message', String, queue_size=1) #Publisher wiadomosci do zapisania w log pojazdu
    level_pub = rospy.Publisher('logtopic/level', Int32, queue_size=1) #Publisher poziomu do zapisania w log pojazdu
    
    while start:
        #Aktywacja licznika powtorzen
        if retry_counter == 0 and start:
            counter_active = True
        while counter_active: #Kiedy licznik aktywny to....
            try:
                #Pingowanie urzadzen
                time.sleep(1)
                # response_router = subprocess.call(['ping', '-c', '3', address_router])
                time.sleep(0.1)
                response_PLC = subprocess.call(['ping', '-c', '3', address_PLC])
                time.sleep(0.1)
                response_FlexiCPU = subprocess.call(['ping', '-c', '3', address_FlexiCPU])
                time.sleep(0.1)
                response_Lidarloc = subprocess.call(['ping', '-c', '3', address_Lidarloc])
                time.sleep(0.1)
                # response_Scanner_1 = subprocess.call(['ping', '-c', '3', address_Scanner_1])
                # time.sleep(0.1)
                # response_Scanner_2 = subprocess.call(['ping', '-c', '3', address_Scanner_2])
                #Zapis wiadomosci odpowiedzi poszczegolnych urzadzen
                # if response_router == 0:
                #     message_0 = ("Router connection: OK")
                # else:
                #     message_0 = ("Router connection: NOT OK, ")
                if response_PLC == 0:
                    message_1 = ("PLC connection: OK")
                else:
                    message_1 = ("PLC connection: NOT OK, ")
                if response_FlexiCPU == 0:
                    message_2 = ("FlexiCPU connection: OK")
                else:
                    message_2 = ("FlexiCPU connection: NOT OK, ")
                if response_Lidarloc == 0:
                    message_3 = ("Lidarloc connection: OK")
                else:
                    message_3 = ("Lidarloc connection: NOT OK, ")
                # if response_Scanner_1 == 0:
                #     message_4 = ("Scanner_1 connection: OK, ")
                # else:
                #     message_4 = ("Scanner_1 connection: NOT OK, ")
                # if response_Scanner_2 == 0:
                #     message_5 = ("Scanner_2 connection: OK")
                # else:
                #     message_5 = ("Scanner_2 connection: NOT OK")
                #Dodanie wszystkich odpowiedzi urzadzen
                responce_all = response_PLC + response_FlexiCPU + response_Lidarloc 
                #Jesli brak problemow z komunikacja
                if responce_all == 0:
                    ping_status = True #Status pingowania
                    #Wylaczenie licznika i zakonczenie procesu pingowania
                    start = False 
                    counter_active = False
                    #Przygotowanie wiadomosci do logowania z poziomem 2 (INFO)
                    message =  message_1 + message_2 + message_3 
                    level = 2
                #Jesli pojawi sie problem z komunikacja
                elif responce_all != 0:
                    ping_status = False #Status pingowania
                    #PRzygotowanie wiadomosci do logowania z poziomem 5 (CRITICAL)
                    message =  message_1 + message_2 + message_3 
                    level = 5 
            except(rospy.ServiceException, rospy.ROSException) as e: #Przypadek bledu z poziomu ros
                message = (e)
                level = 5
            retry_counter = retry_counter + 1 #Dodanie do licznika "1" po przejsciu proby
            #Dezaktywacja funkcji jesli przekroczymy x prob.
            if retry_counter == 2:
                counter_active = False
                start = False
    #Po dezaktywacji pingowania opublikowanie wiadomosci ping_status oraz logow do zapisu
    while not start:
        ping_status = True
        ping_status_pub.publish(ping_status)
        message_pub.publish(message)
        level_pub.publish(level)
        time.sleep(10)
        break
if __name__ == '__main__':
    try:
        c = check_connection()
    except rospy.ROSInterruptException as e:
        rospy.logerr(": %s" % e)
    finally:
        rospy.loginfo_once('ping finished')