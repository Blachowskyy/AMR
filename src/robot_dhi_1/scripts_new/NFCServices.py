#!/usr/bin/env python3

import rospy
import time
import xml.etree.ElementTree as ET
from std_msgs.msg import Bool, String
from smartcard.CardMonitoring import CardObserver, CardMonitor
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException
from robot_dhi_1.msg import FlexiReads
class PrintObserver(CardObserver):
    #Osobna klasa obslugujaca czytnik kart NFC
    def __init__(self, nfc_instance):
        #Polaczenie do klasy obejmujacej logike
        super(PrintObserver, self).__init__()
        self.nfc = nfc_instance
    def update(self, observable, actions):
        (addedcards, removedcards) = actions #Dodanie akcji dotyhczacych kart ( przylozenie i odciagniecie)
        for card in addedcards:
            for _ in range(10):  
                try:
                    card.connection = card.createConnection() #Stworzenie polaczenia z karta
                    card.connection.connect() #Aktywacaj polaczenia z karta
                    response, sw1, sw2 = card.connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00]) #Bity komunikacyjne z karta
                    if sw1 == 0x90:
                        self.nfc.card_readed = toHexString(response) #Odczyt UID 4bit karty
                    else:
                        self.nfc.card_readed = None #Gdy blad poolaczenia skasowanie aktywnej karty
                    break
                except (NoCardException, CardConnectionException):
                    time.sleep(0.5)
                    if self.nfc.card_readed is not None: # obsluga 10 krotnej proby polaczenia w przypadku bledow karty
                        break
                    continue
        for card in removedcards:
            self.nfc.card_read_end = True #Potwierdzenie zakonczenia odczytu karty po zniknieciu z pola czytnika
class NFC:
    def __init__(self):
        self.init_nfc()
    def init_nfc(self): 
        #Inicjacja zmiennych uzywanych w programie
        self.card_active = None
        self.card_readed = None
        self.card_read_end = False
        #Inicjacja kart
        self.cardmonitor = CardMonitor()
        self.cardobserver = PrintObserver(self)
        self.cardmonitor.addObserver(self.cardobserver)
        self.xml_card_id = None
        self.xml_username = None
        self.xml_accesslevel = None
        self.user_active_card_id = None
        self.user_active_name = None
        self.user_active_accesslevel = None
        self.user_logged = False
        self.safety_state = FlexiReads()
        self.last_received_time = None
        self.reset_to_auto_mode = False
        self.first_run = True
        self.workstate_status = False
        self.user_present = False
        self.rate = rospy.Rate(30) #odswiezanie 3
        rospy.loginfo_once('NFC services started...')
        while not rospy.is_shutdown():
            try:
                #Inicjacja topiciow
                self.safety_state_sub = rospy.Subscriber('Forklift/state/safety/safety_status', FlexiReads, self.safety_status_callback)
                self.reset_auto_sub = rospy.Subscriber('Forklift/state/user/reinitialize_auto', Bool, self.re_auto_callback)

                self.user_logged_pub = rospy.Publisher('Forklift/state/user/login_status', Bool, queue_size=1,latch=True)
                self.user_card_id_pub = rospy.Publisher('Forklift/state/user/card_id', String, queue_size=1,latch=True)
                self.user_access_level_pub = rospy.Publisher('Forklift/state/user/acces_level', String, queue_size=1,latch=True)
            except (rospy.ServiceException, rospy.ROSException) as e:
                rospy.loginfo(e)
            self.process_card() #Obsluga logiki
            self.rate.sleep() #Odswiezanie

    def re_auto_callback(self,msg):
        self.reset_to_auto_mode = msg.data
    def safety_status_callback(self, msg):
        self.safety_state = msg 
    def process_card(self):
        if self.card_read_end and not self.user_logged and (not self.safety_state.LeftScannerReducedSpeedZoneStatus or not self.safety_state.RightScannerReducedSpeedZoneStatus):
            rospy.loginfo_once('Starting card reading....')
            self.card_readed = str(self.card_readed) #konwersja UID karty na string
            self.xml_read() #Obsluga pliku xml 
        if self.user_logged:
            #publikowanie aktywnego uzytkownika po udanym logowaniu
            rospy.loginfo_once('User logged!')
            rospy.loginfo_once(self.safety_state)
            self.publish_user()
            if self.user_logged and self.safety_state.LeftScannerReducedSpeedZoneStatus and self.safety_state.RightScannerReducedSpeedZoneStatus:
                time.sleep(4)
                if self.user_logged and self.safety_state.LeftScannerReducedSpeedZoneStatus and self.safety_state.RightScannerReducedSpeedZoneStatus:
                    self.first_run = False
                    self.logout()
                    self.publish_user()
                    rospy.loginfo_once('User logged out...')
    def publish_user(self):
        self.user_access_level_pub.publish(self.user_active_accesslevel) # publikacja poziomu dostepu
        time.sleep(0.1)
        self.user_card_id_pub.publish(self.user_active_card_id) # publikacja UID karty uzytkownika
        time.sleep(0.1)
        self.user_logged_pub.publish(self.user_logged)  #publikacja statusu logowania
    def xml_read(self):
        #Odczyt z pliku xml wszystkich uzytkownikow z uprawnieniami
        rospy.loginfo_once('Starting parsing user list...')
        tree = ET.parse("/home/ros/catkin_ws/src/robot_dhi_1/scripts_new/users.xml") 
        root = tree.getroot()
        for card_element in root.findall("card"):
            self.xml_card_id = card_element.find("atr").text
            #Logowanie gdy odczytane UID karty = UID odnalezione w pliku xml
            if self.xml_card_id == self.card_readed and (not self.safety_state.LeftScannerReducedSpeedZoneStatus or not self.safety_state.RightScannerReducedSpeedZoneStatus):
                #Przypisanie danych aktywnego uzytkownika gdy znajduje sie w xml oraz jest w strefie 
                rospy.loginfo_once("Zalogowano uzytkownika:")
                self.user_active_card_id = self.xml_card_id
                self.user_active_name = card_element.find("name").text
                self.user_active_accesslevel = card_element.find("accesslevel").text
                self.user_logged = True         
    def logout(self):
        #Wylogowanie i wyczyszczenie zmiennych do stanu poczatkowego
        #w celu ponownej mozliwosci zalogowania
        self.user_logged = False
        self.xml_card_id = None
        self.xml_username = None
        self.xml_accesslevel = None
        self.user_active_card_id = None
        self.user_active_name = None
        self.user_active_accesslevel = None
        self.card_active = None
        self.card_readed = None 
        rospy.loginfo_once("Operator logged out")
if __name__ == '__main__':
    rospy.init_node('nfc_services') #Inicjacja node'a
    try:
        nfc = NFC() #inicjacja klasy glownej 
    except KeyboardInterrupt:
        pass
    finally:
        rospy.loginfo("+++++++++++++OUT++++++++++")
