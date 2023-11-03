#!/usr/bin/env python3
import rospy
from pyModbusTCP.client import ModbusClient as MC
from bitstring import BitArray
from robot_dhi_1.msg import FlexiReads, FlexiWrites, WorkstateRead
import time
class Flexiconnection:
    def __init__(self):
        #Deklaracje zmiennych globalnych
        self.testingPlatform = True
        self.gmod_address = '192.168.1.11'
        self.gmod_port = 502
        self.gmod_writetable = list()
        self.gmod_readlist = list()
        self.data_old = None
        self.send_data1 = BitArray(16)
        self.send_data2 = BitArray(16)
        self.send_data3 = BitArray(16)
        self.send_data4 = BitArray(16)
        self.send_data5 = BitArray(16)
        self.send_word_1 = 0
        self.send_word_2 = 0
        self.send_word_3 = 0
        self.send_word_4 = 0
        self.send_word_5 = 0
        self.send_dataset_1 = [0] * 5
        self.safetyDataReaded = FlexiReads()
        self.safetyDataToWrite = FlexiWrites()
        self.data_bool = list()
        self.active_workstate = WorkstateRead()
        self.scannersCriticalError = False
        
        while not rospy.is_shutdown():
            #Deklaracja polaczenia
            self.gmod_obj = MC(self.gmod_address, self.gmod_port, auto_open=True, auto_close=True)
            try: 
                #deklaracja publishera
                self.safety_pub = rospy.Publisher('Forklift/state/safety/safety_status', FlexiReads, queue_size=1, latch=True) 
                self.safety_sub = rospy.Subscriber('Forklift/control/safety', FlexiWrites, self.Ros_to_Flexi)  
                self.workstate_sub = rospy.Subscriber('Forklift/state/workstates/PLC_active', WorkstateRead, self.workstateCallback) 
            except(rospy.ServiceException, rospy.ROSInternalException):
                rospy.loginfo('error')
            self.gmod_read() # wywolanie odczytu z bramki GMOD
            self.ScannersLogic()    
            self.gmod_write() # spowodowanie zapisu do bramki GMOD
            self.data_bool.clear()
            rospy.loginfo(self.scannersCriticalError)
            # time.sleep(1)
    def workstateCallback(self, msg):
        self.active_workstate = msg
    def Ros_to_Flexi(self, msg):
        self.safetyDataToWrite = msg
    def gmod_write(self):
        self.send_data1[0] = self.safetyDataToWrite.ScannersFieldSignalA1
        self.send_data1[1] = self.safetyDataToWrite.ScannersFieldSignalA2
        self.send_data1[2] = self.safetyDataToWrite.ScannersFieldSignalB1
        self.send_data1[3] = self.safetyDataToWrite.ScannersFieldSignalB2
        self.send_data1[4] = self.safetyDataToWrite.RightScannerResetConnection
        self.send_data1[5] = self.safetyDataToWrite.RightScannerReset
        self.send_data1[6] = self.safetyDataToWrite.LeftScannerResetConnection
        self.send_data1[7] = self.safetyDataToWrite.LeftScannerReset
        self.send_data1[8] = self.safetyDataToWrite.ScannersActivate
        self.send_data1[9] = self.safetyDataToWrite.RightScannerResetReducedSpeedField
        self.send_data1[10] = self.safetyDataToWrite.RightScannerResetSoftStopField
        self.send_data1[11] = self.safetyDataToWrite.RightScannerResetEmergencyField
        self.send_data1[12] = self.safetyDataToWrite.LeftScannerResetReducedSpeedField
        self.send_data1[13] = self.safetyDataToWrite.LeftScannerResetSoftStopField
        self.send_data1[14] = self.safetyDataToWrite.LeftScanerResetEmergencyField
        self.send_data1[15] = False # Aktywacja skanerow, zawsze wartosc TRUE    
        for bit in self.send_data1:
            self.send_word_1 = (self.send_word_1 << 1) | bit
        #Podzial wysylanych danych na wordy po 16 bitow 
        self.send_dataset_1[0] = self.send_word_1
        self.send_dataset_1[1] = self.send_word_2
        self.send_dataset_1[2] = self.send_word_3
        self.send_dataset_1[3] = self.send_word_4
        self.send_dataset_1[4] = self.send_word_5
        #przeslanie listy wordow, zmienna test = true, gdy zapis udany
        test = self.gmod_obj.write_multiple_registers(2099, self.send_dataset_1)
        self.send_word_1 = 0
        # print(test)
    def gmod_read(self):
        data = bytearray()
        # 999 adres do odczytu wszystkich danych, po przecinku ilosc wordow ( dokumentacja sick )
        data = self.gmod_obj.read_holding_registers(999,25)
        #wYWOLANIE FUNKCJI TYLKO W PRZYPADKU ZMIANY DANYCH
        
        data_bin = list()
        for item in data:
            data_bin.append(bin(int(item)))
        data = list()
        data = self.process_signal(data_bin)
        for i in range(0, len(data)):
            self.data_bool.append(bool(int(data[i])))
        if len(self.data_bool) > 0:
            
            self.safetyDataReaded.LeftEmergencyStopStatus = self.data_bool[0]
            self.safetyDataReaded.RightEmergencyStopStatus = self.data_bool[1]
            self.safetyDataReaded.LeftLidarActive = self.data_bool[2]
            self.safetyDataReaded.RightLidarActive = self.data_bool[3]
            self.safetyDataReaded.SafeSpeed = self.data_bool[4]
            self.safetyDataReaded.EncoderOK = self.data_bool[5]
            self.safetyDataReaded.CpuOK = self.data_bool[6]
            self.safetyDataReaded.Standstill = self.data_bool[7]
            self.safetyDataReaded.LeftScannerEmergencyZoneStatus = self.data_bool[8]
            self.safetyDataReaded.LeftScannerSoftStopZoneStatus = self.data_bool[9]
            self.safetyDataReaded.LeftScannerReducedSpeedZoneStatus = self.data_bool[10]
            self.safetyDataReaded.RightScannerEmergencyZoneStatus = self.data_bool[11]
            self.safetyDataReaded.RightScannerSoftStopZoneStatus = self.data_bool[12]
            self.safetyDataReaded.RightScannerReducedSpeedZoneStatus = self.data_bool[13]
            self.safetyDataReaded.LeftScannerContaminationWarning = self.data_bool[14]
            self.safetyDataReaded.LeftScannerContaminationError = self.data_bool[15]
            self.safetyDataReaded.RightScannerContaminationWarning = self.data_bool[16]
            self.safetyDataReaded.RightScannerContaminationError = self.data_bool[17]
            self.safetyDataReaded.LeftScannerAppError = self.data_bool[18]
            self.safetyDataReaded.LeftScannerDeviceError = self.data_bool[19]
            self.safetyDataReaded.RightScannerAppError = self.data_bool[20]
            self.safetyDataReaded.RightScannerDeviceError = self.data_bool[21]
            
            for i in range(8, 14):
                self.safetyDataReaded.UserNotDetected = self.safetyDataReaded.UserNotDetected + self.data_bool[i]
            self.safety_pub.publish(self.safetyDataReaded)
            
    def process_signal(self,data_bin):
        data_bin_len = len(data_bin)
        tmp = list()
        tmp2 = ''
        for i in range (0, data_bin_len):
            data_bin[i] = data_bin[i][2:]
            diff = 16 - len(data_bin[i])
            for j in range (0, diff):
                data_bin[i] = "0" + data_bin[i]
            data_bin[i] = data_bin[i][::-1]
            tmp.append(data_bin[i])
        for i in range(0, len(tmp)):
            tmp2 = tmp2 + tmp[i]
        result = list(tmp2)
        return result
        
    def ScannersLogic(self):
        # print(self.active_workstate)
        self.safetyDataToWrite.ScannersActivate = True
        if self.safetyDataReaded.LeftScannerDeviceError or self.safetyDataReaded.LeftScannerAppError or self.safetyDataReaded.RightScannerDeviceError or self.safetyDataReaded.RightScannerAppError:
            self.scannersCriticalError = self.ScannerReset()
        if self.active_workstate.S0_1:
            self.safetyDataToWrite.ScannersFieldSignalA1 = True
            self.safetyDataToWrite.ScannersFieldSignalA2 = False
            self.safetyDataToWrite.ScannersFieldSignalB1 = True
            self.safetyDataToWrite.ScannersFieldSignalB2 = False
        if self.active_workstate.S0_3:
            self.safetyDataToWrite.ScannersFieldSignalA1 = True
            self.safetyDataToWrite.ScannersFieldSignalA2 = False
            self.safetyDataToWrite.ScannersFieldSignalB1 = False
            self.safetyDataToWrite.ScannersFieldSignalB2 = True
        if self.active_workstate.S4_1:
            if not self.testingPlatform:
                self.safetyDataToWrite.ScannersFieldSignalA1 = False
                self.safetyDataToWrite.ScannersFieldSignalA2 = True
                self.safetyDataToWrite.ScannersFieldSignalB1 = True
                self.safetyDataToWrite.ScannersFieldSignalB2 = False
            if self.testingPlatform:
                self.safetyDataToWrite.ScannersFieldSignalA1 = False
                self.safetyDataToWrite.ScannersFieldSignalA2 = True
                self.safetyDataToWrite.ScannersFieldSignalB1 = False
                self.safetyDataToWrite.ScannersFieldSignalB2 = True
        if self.active_workstate.S4 and not self.active_workstate.S4_1:
            self.safetyDataToWrite.ScannersFieldSignalA1 = False
            self.safetyDataToWrite.ScannersFieldSignalA2 = True
            self.safetyDataToWrite.ScannersFieldSignalB1 = False
            self.safetyDataToWrite.ScannersFieldSignalB2 = True
    def ScannerReset(self):
        self.safetyDataToWrite.LeftScannerReset = True
        self.safetyDataToWrite.RightScannerReset = True
        self.gmod_write()
        time.sleep(0.1)
        self.gmod_read()
        if self.safetyDataReaded.LeftScannerDeviceError or self.safetyDataReaded.LeftScannerAppError or self.safetyDataReaded.RightScannerDeviceError or self.safetyDataReaded.RightScannerAppError:
            self.safetyDataToWrite.LeftScannerResetConnection = True
            self.safetyDataToWrite.RightScannerResetConnection = True
            self.gmod_write()
            time.sleep(0.1)
        self.safetyDataToWrite.LeftScannerReset = False
        self.safetyDataToWrite.RightScannerReset = False
        self.safetyDataToWrite.LeftScannerResetConnection = False
        self.safetyDataToWrite.RightScannerResetConnection = False
        self.gmod_write()
        rospy.loginfo('Waiting for scanners to reset fully...')
        time.sleep(5)
        self.gmod_read()
        if self.safetyDataReaded.LeftScannerDeviceError or self.safetyDataReaded.LeftScannerAppError or self.safetyDataReaded.RightScannerDeviceError or self.safetyDataReaded.RightScannerAppError:
            return False
        else:
            return True
        rospy.loginfo("RESET SKANERA")  
if __name__ == '__main__':
    try:
        rospy.init_node('flexicpu')
        flexiconnection = Flexiconnection()
        rospy.spin()
    except rospy.ROSInterruptException as e:
        rospy.logerr("Flexi error: %s" % e)