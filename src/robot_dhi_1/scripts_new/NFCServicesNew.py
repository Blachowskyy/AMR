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
        self.rate = rospy.Rate(0.1) #odswiezanie 3
        rospy.loginfo_once('NFC services started...')
        while not rospy.is_shutdown():
            try:
                #Inicjacja topiciow
                self.CardPub = rospy.Publisher('Forklift/state/user/card_id', String, queue_size=1,latch=True)
            except (rospy.ServiceException, rospy.ROSException) as e:
                rospy.loginfo(e)
            self.ProcessCard() #Obsluga logiki
            self.rate.sleep() #Odswiezanie

    def ProcessCard(self):
        if (self.card_readed != None):
            message = str(self.card_readed)
            self.CardPub.publish(message)
            self.card_readed = None
            message = str(self.card_readed)
            time.sleep(60)
            self.CardPub.publish()
    
if __name__ == '__main__':
    rospy.init_node('nfc_services') #Inicjacja node'a
    try:
        nfc = NFC() #inicjacja klasy glownej 
    except KeyboardInterrupt:
        pass
    finally:
        rospy.loginfo("+++++++++++++OUT++++++++++")
