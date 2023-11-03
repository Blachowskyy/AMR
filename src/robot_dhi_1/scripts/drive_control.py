#!/usr/bin/env python3

import threading
import math
from time import sleep
from pyModbusTCP import client
import rospy
from std_msgs.msg import Int64, Float32

# Do zadawania jazdy wykorzystujemy rejestry %MW101 i %MW102. 
# Rejestr %MW102 przyjmuje wartość 5 lub 6 lub 0 co oznacza kierunek jazdy. 
# 2 to jazda do przodu, 
# 1 to jazda do tyłu, 
# 0 to stop. 
# Rejestr %MW101 przyjmuje wartość 0-4000  prędkość jazdy

class WozekModbusDriver:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.mutex = threading.Lock()
        self.Wozek_Stop = 0
        self.Wozek_do_Tylu = 1 
        self.Wozek_do_Przodu = 2 

        self.Servo_Off = 3333
        self.Servo_On = 4444
        self.Servo_Obrot =  5
        self.direction = 0
        self.speed = 0
        self.wysokosc_widel = 0
        
        self.waga = 0
        self.przechyl_bok = 0
        self.przechyl_wzdluz = 0
        self.waga_critical = False
        self.cargo = False
        self.przechyl_danger = False
        self.check_position = False

        #Deklaracje subskrybcji wiadomosci z systemu ROS
        try:
            self.deltaPLC = client.ModbusClient(host='192.168.1.4', port=502, auto_open=True, auto_close=True)
            rospy.loginfo("Modbus setup complete")
            self.curtis_sub = rospy.Subscriber('comand_curtis_vel', Int64, self.wozekCallback, queue_size = 1) 
            self.servo_sub = rospy.Subscriber('comand_servo_angle', Float32, self.servoCallback, queue_size = 1)
            # self.high_sub = rospy.Subscriber('command_high', Int64, self.heightCallback)
            self.wysokos_sub = rospy.Subscriber('wyokosc_widel', Int64, self.reads_high)
            self.preessure_sub = rospy.Subscriber('czujnik_cisnienia', Int64, self.reads_presure)
            self.przechyl_bok_sub = rospy.Subscriber('czujnik_przechylu_w_bok', Int64, self.reads_przechyl_bok)
            self.przeychyl_wzdluz_sub = rospy.Subscriber('czujnik_przechylu_wzdluz', Int64, self.reads_przechyl_wzdluz)
            self.encoder_sub = rospy.Subscriber('wozek_angle_tick', Float32, self.reads_speed)
            self.servo_position_sub = rospy.Subscriber('servo_angle_tick', Float32, self.reads_position)
            # self.deltaPLC.write_single_register(110, 1)

            self.test_pub = rospy.Publisher('drive_controler_PWM', Int64, queue_size=1)
            self.test2_pub = rospy.Publisher('drive_controler_PWM_callback', Int64, queue_size=1)
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("connect/subscribers/publishers: %s" % e)

    def reads_position(self, msg):
        self.servo_actual_position = msg.data

    #Modul odczytu wiadomosci o przejechanej drodze z pliku detectors.py
    def reads_speed(self, msg):
        self.speed_actual = msg.data

    #Modul odczytu wiadomosci o aktualnej pozycji widel z pliku detectors.py
    def reads_high(self, msg):
        self.wysokosc_widel = msg.data

    #Modul odczytu wiadomosci o wadze znajdujacej sie na widlach  z pliku detectors.py    
    def reads_presure(self, msg):
        self.waga = msg.data

    #Modul odczytu wiadomosci o przechyle w bok z pliku detectors.py
    def reads_przechyl_bok(self, msg):
        self.przechyl_bok = msg.data

    #Modul odczytu wiadomosci o przechyle wzdluz z pliku detectors.py
    def reads_przechyl_wzdluz(self, msg):
        self.przechyl_wzdluz = msg.data

    def validation_przechyly(self):
        if (self.przechyl_bok <= -10 or self.przechyl_bok >= 10):
            self.przechyl_danger = True
        elif (self.przechyl_wzdluz <=10 or self.przechyl_wzdluz >= 10):
            self.przechyl_danger = True
        else:
            self.przechyl_danger = False
        
    #Modul wykonujacy polecenie ruchu widlami
    # def steering_widly(self, widly_height, wysokosc_widel, speed_actual, waga_critical, cargo):
    #     self.is_in_motion = False
    #     motion1 = 0
    #     motion2 = 0
    #     blockade = False
    #     memory_ostatni = 0
    #     self.mutex.acquire(blocking=True)
    #     rate = rospy.Rate(5)
    #     rospy.loginfo(f'Sterowanie wysokoscia {self.wysokosc_widel}' )
    #     try:
    #         motion1 = self.speed_actual
    #         rate.sleep()
    #         motion2 = self.speed_actual
    #         if (motion1 == motion2):
    #             self.is_in_motion = False
    #         elif (motion1 != motion2):
    #             self.is_in_motion = True
    #     except:
    #         rospy.loginfo('blad kontroli ruchu wuzka')
    #     try:
            
    #         if (self.widly_height < 109):
    #             self.widly_height = 109
    #         elif (self.widly_height > 209):
    #             self.widly_height = 209
    #         else:
    #             self.widly_height = self.widly_height
    #     except:
    #         rospy.loginfo('blad kontroli wprowadzanej wysokosci')
    #     try:
    #         memory_ostatni = self.deltaPLC.read_holding_registers(2000, 1)
    #         rospy.loginfo(memory_ostatni)
    #         if (self.widly_height == memory_ostatni[0]):
    #             blockade = True
    #             rospy.loginfo(blockade)
    #         elif (self.widly_height != memory_ostatni[0]):
    #             blockade = False
    #     except:
    #         rospy.loginfo('blad kontroli wprowadzanej wysokosci')
    #         #Cala logika podnoszenia wideł do poprawy - to do!
    #     if (self.is_in_motion == False and blockade == False):
    #         if (self.widly_height < self.wysokosc_widel):
    #             self.deltaPLC.write_single_register(105, 1)
    #             self.deltaPLC.write_single_register(104, self.widly_height)
    #             self.validation_przechyly()
    #             if (self.przechyl_danger == True):
    #                 self.deltaPLC.write_single_register(105, 0)
    #                 self.deltaPLC.write_single_register(104, 0) 
    #             sleep(5)
    #             self.WagaControl()
    #             if (self.cargo == True):
    #                 rospy.loginfo('Blad odlozenia ladunku')
    #             else:
    #                 rospy.loginfo('Odlozylem ladunek')
    #         elif (self.widly_height > self.wysokosc_widel):
    #             self.deltaPLC.write_single_register(105, 2)
    #             self.deltaPLC.write_single_register(104, self.widly_height)
    #             self.validation_przechyly()
    #             # if (self.przechyl_danger == True):
    #             #     self.deltaPLC.write_single_register(2000, 0)
    #             #     self.deltaPLC.write_single_register(2001, 0) 
                
    #             sleep(10)
    #             # self.widly_height = self.widly_height - 1
    #             # self.deltaPLC.write_single_register(2000, self.widly_height)
    #             self.deltaPLC.write_single_register(105, 3)
    #             self.WagaControl()
    #             rospy.loginfo(self.cargo)
    #             if (self.cargo == True and self.waga_critical == False):
    #                 rospy.loginfo('Podnioslem ladunek, wszystko w normie')
    #             elif (self.cargo == True and self.waga_critical == True):
    #                 rospy.loginfo('Podniesiony ladunek jest zbyt ciezki - opuszczam widly')
    #                 self.widly_height = 109
    #                 self.deltaPLC.write_single_register(105, 1)
    #                 self.deltaPLC.write_single_register(104, self.widly_height)
    #             elif ( self.cargo == False):
    #                 rospy.loginfo('Blad podnoszenia ladunku - brak ladunku - opuszczam widly')
    #                 self.widly_height = 109
    #                 self.deltaPLC.write_single_register(105, 1)
    #                 self.deltaPLC.write_single_register(104, self.widly_height)

    #         else:
    #             self.deltaPLC.write_single_register(105, 0)
    #             self.deltaPLC.write_single_register(104, self.widly_height)
    #         rospy.loginfo(f'Wysokosc zadana {self.widly_height}')

    #     elif (self.is_in_motion == True):
    #         rospy.loginfo('Kontrola widel zablokowana przez jazde! Zatrzymaj sie ')
    #     elif (blockade == True):
    #         rospy.loginfo('Podales ostatnio wprowadzana wartosc')

    #     self.mutex.release()

    #Modul autokontroli polaczenia
    def validation_connection(self):
        try:
            while self.deltaPLC.is_open() == False:
                rospy.loginfo('Try connect')
                self.deltaPLC = client.ModbusClient('192.168.1.5', 502)
                self.deltaPLC.open()
        except:
            rospy.loginfo('Delta PLC has no connection')
    
    #Modul zaokraglajacy wartosc kata do 2 miejsc po przecinku i pozbywajacy sie przecinka
    def validation_angle_impulses(self):
        self.angle_impulses = round(self.angle_impulses, 2) * 100
        self.angle_impulses = math.trunc(self.angle_impulses)

    #Modul kontroli podnoszonej wagi oraz obecnosci ladunku                
    def WagaControl(self,):
        if (self.waga >= 1500 or self.waga > 10):
            self.waga_critical = False
            self.cargo = True
        elif(self.waga < 10 or self.waga >= 0):
            self.waga_critical = False
            self.cargo = False
        elif(self.waga > 1500):
            self.waga_critical = True
            self.cargo = True
        elif(self.waga < 0):
            rospy.loginfo("prawdopodobne uszkodzenie modulu podnoszenia badz blad funkcji")
        
    #Modul wykonujacy polecenie skretu kola
    def MoveServo(self, angle_impulses, action_type):
        self.deltaPLC.write_single_register(109, 1)
        pose = (f'Servo Pozycja {self.angle_impulses}')
        self.mutex.acquire(blocking=True)
        try:
            if self.angle_impulses == self.Servo_Off: 
                self.deltaPLC.write_single_register(109, 0)
                rospy.loginfo('Servo Off')
            elif self.angle_impulses == self.Servo_On: 
                self.deltaPLC.write_single_register(109, 1)
                rospy.loginfo('Servo On')
            elif self.angle_impulses != (self.Servo_Off):
                if (self.angle_impulses < 0 and self.angle_impulses >= -70): 
                    self.validation_angle_impulses()
                    rospy.loginfo('minus')
                    self.angle_impulses = self.angle_impulses * -1
                    self.deltaPLC.write_single_register(108, self.angle_impulses)
                    self.deltaPLC.write_single_register(107, 1)
                    rospy.loginfo(pose)
                elif (self.angle_impulses >= 0 and self.angle_impulses <= 70):
                    self.validation_angle_impulses()
                    rospy.loginfo('plus')
                    # self.angle_impulses = self.angle_impulses * -1
                    self.deltaPLC.write_single_register(108, self.angle_impulses)
                    self.deltaPLC.write_single_register(107, 2)
                    rospy.loginfo(pose)
                else: 
                    rospy.loginfo("Value must be in range from -70 to 70")
                # self.deltaPLC.write_single_register(106, 15)
                # self.deltaPLC.write_single_register(110, 1)
                self.deltaPLC.write_single_register(109, 5)
                sleep(0.5)
                # self.deltaPLC.write_single_register(109, 5)
                # self.check_position = True
            self.mutex.release()
            
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("MoveServo call failed: %s" % e)
            return False 

    #Modul wykonujacy polecenie kierunku i predkosci jazdy
    def MoveMotor(self, direction, speed):
        self.mutex.acquire(blocking=True)
        rospy.loginfo('MoveMotor')
        max_speed =1200
        raczka = self.deltaPLC.read_coils(24576, 1)
        try:
            if self.direction == self.Wozek_do_Przodu:
                # if self.speed >0 and self.speed < 450:
                #     self.speed = 0
                #     self.direction = self.Wozek_Stop
                # if self.speed >= 200 and self.speed <= 500:
                #     self.speed = 500
                if self.speed >= max_speed:
                    self.speed = max_speed
                elif self.speed > 450 and self.speed < max_speed:
                    self.speed = self.speed  

            elif self.direction == self.Wozek_do_Tylu:
                # if self.speed < 0 and self.speed > -450:
                #     self.speed = 0
                #     self.direction = self.Wozek_Stop
                # if self.speed <= -200 and self.speed >= -500:
                #     self.speed = 500
                if self.speed <= -max_speed:
                    self.speed = max_speed 
                elif self.speed < -450 and self.speed > -max_speed:
                    self.speed = -self.speed 
                    
            elif raczka == True:
                self.speed = 0
                self.direction = self.Wozek_Stop

            else:
                self.direction = self.Wozek_Stop
                self.speed = 0
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("MoveMotor call failed: %s" % e)
            return False 
        self.deltaPLC.write_single_register(102, self.direction)
        self.deltaPLC.write_single_register(101, self.speed)
        test = self.speed
        self.mutex.release()
        self.test_pub.publish(test)
        
        rospy.loginfo(f'Predkosc {self.speed} czynnosc {self.direction}')

    #Modul przyjmujacy polecenia sterowania widlami
    # def heightCallback(self, msg):
    #     try:
    #         self.widly_height = msg.data
    #         rospy.loginfo('height Callback')
    #         self.steering_widly(self.widly_height, self.wysokosc_widel, self.speed_actual, self.waga_critical, self.cargo)
    #     except (rospy.ServiceException, rospy.ROSException) as e:
    #         rospy.loginfo("heightCallback call failed: %s" % e)
    #         return False

    #Modul przyjmujacy polecenia skretu kolem
    def servoCallback(self, msg):
        try:
            servo_position_tmp = 0.0
            self.angle_impulses = msg.data
      
            self.servoAngle = self.angle_impulses
            rospy.loginfo('Servo Callback')
            
            self.MoveServo(self.angle_impulses, self.servoAngle)
            while (self.check_position == True):
                
                servoAngle_tmp = round(self.servoAngle, 2) * 100
                servoAngle_tmp = math.trunc(servoAngle_tmp)
                # if self.servo_actual_position == -0.0:
                #     servo_position_tmp == 0.0
                # else:
                servo_position_tmp = self.servo_actual_position
                servo_position_tmp = round(servo_position_tmp, 2) * 100
                servo_position_tmp = math.trunc(servo_position_tmp)

                if ( servo_position_tmp == servoAngle_tmp):
                    rospy.loginfo("Osiagnieto pozytcje")
                    self.check_position = False
                # elif ( servo_position_tmp != servoAngle_tmp):
                    

        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("servoCallback call failed: %s" % e)
            return False

    #Modul przyjmujacy polecenia dotyczace jazdy i okreslajacy jej kierunek
    def wozekCallback(self, msg): 
        self.speed = msg.data
        rospy.loginfo('wozekCallback')
        test = self.speed
        self.test2_pub.publish(test)
        
        
        try:
            if self.speed > 450:
                self.direction = self.Wozek_do_Przodu
            elif self.speed < -450:
                self.direction = self.Wozek_do_Tylu
            
            else:
                self.speed = 0
                self.direction = self.Wozek_Stop
            
            self.MoveMotor(self.direction, self.speed)
            return 
            
        except (rospy.ServiceException, rospy.ROSException) as e:
            rospy.logerr("wozekCallback call failed: %s" % e)
            return False

            
if __name__ == '__main__':
    try:    
        rospy.init_node('wozek')
        wozek = WozekModbusDriver()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
        
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')