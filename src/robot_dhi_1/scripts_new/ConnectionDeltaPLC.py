#!/usr/bin/env python3
import threading
import os
from time import sleep
from pyModbusTCP import client
import rospy
from std_msgs.msg import Int64, String, Bool, Int32, Int64MultiArray, ByteMultiArray
from robot_dhi_1.msg import WorkstateRead as WR, WorkstateSelect as WS
from robot_dhi_1.msg import DistanceDrive as DD, Scangrids
# Program komunikacyjny ROS <--> PLC
class PLC:
    def __init__(self):
        #Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.mutex = threading.Lock()
        #Lists
        self.WriteDataTable = [0] * 99
        self.ReadDataTable = [0] * 99
        self.ErrorIdTable = [0] * 10
        self.VirtualIOTable = [0] * 10
        self.SignalsInTable = [None] * 80
        self.SignalsOutTable = [False] * 80
        self.TempWorkstatesInTable = []
        self.SignalsInTableOld = [False] * 80
        self.SignalsOutTableOld = [False] * 80
        self.ReadedIOTable = [False] * 80
        self.Errors = [0] * 99
        #Custom data
        self.WorkstatesFromROS = WS()
        self.WorkstatesReadedPLC = WR()
        self.DistanceSend = DD()
        self.DistanceRead = DD()
        self.LastDistanceSend = DD()
        self.ScangridsDataIn = Scangrids()
        self.ScangridsDataOut = Scangrids()
        #string
        self.LogMessage = ''
        #Int
        self.CurtisPWM = 0
        self.CurtisDirection = 0
        self.ServoAngle = 0
        self.ServoDirection = 0
        self.ServoOFF = 0
        self.GiveWorkstate = 1
        self.ServoPower = 0
        self.Distance = 0
        self.ErrorCode = 0
        self.LogLEvel = 0
        self.ForksCommand = 0
        self.Watchdog = 1
        self.WatchdogOld= 0
        #Bool
        self.ScangridsActivator = False
        self.OperatorResetAutoMode = False
        self.OperatorLoggedIn = False
        self.ConnectionPLC = True
        self.rate = rospy.Rate(30) # 30Hz
        self.Clear = lambda: os.system('clear')
        self.DeltaPLC = client.ModbusClient("192.168.1.4", 502, auto_close=True, auto_open=True)
        self.Plc_connect()
        while not rospy.is_shutdown():
            try:
                #Deklaracje publikowanych i odczytywanych topicow ROS ( publikujemy dane PLC, odczytujemy dane do zapisu w PLC)
                self.ForkHeightPub = rospy.Publisher('PLC/read/fork_height', Int64, queue_size=1)
                self.CargoWeightPub = rospy.Publisher('PLC/read/cargo_weight', Int64, queue_size=1)
                self.TiltAxis1Pub = rospy.Publisher('PLC/read/tilt_axis_1', Int64, queue_size=1)
                self.TiltAxis2Pub = rospy.Publisher('PLC/read/tilt_axis_2', Int64, queue_size=1)
                self.BatteryVoltagePub = rospy.Publisher('PLC/read/battery_voltage', Int64, queue_size=1)
                self.EncoderSpeedPub = rospy.Publisher('PLC/read/encoder_speed', Int64, queue_size=1)
                self.EncoderDirectionPub = rospy.Publisher('PLC/read/encoder_direction', Int64, queue_size=1)
                self.ForksHeightLimiterStatusPub = rospy.Publisher('PLC/read/forks_height_limiter', Int64, queue_size=1)
                self.ServoActualDirectionPub = rospy.Publisher('PLC/read/servo_direction', Int64, queue_size=1)
                self.ServoActualAnglePub = rospy.Publisher('PLC/read/servo_angle', Int64, queue_size=1)
                self.LogMessagePub = rospy.Publisher('log/message', String, queue_size=10)
                self.LogLEvelPub = rospy.Publisher('log/level', Int32, queue_size=10)
                self.ScangridsDataOutPub = rospy.Publisher('Forklift/Scangrids/DataOut', Scangrids, queue_size=1, latch=True)
                self.ActiveWorkstatePub = rospy.Publisher('Forklift/state/workstates/Active', WR, queue_size=1, latch=True)
                self.ReinitializeAutoModePub = rospy.Publisher('Forklift/state/user/reinitialise_auto', Bool, queue_size=1)
                self.DistanceReadPub = rospy.Publisher('PLC/read/distance', Int64, queue_size=1)
                self.DistanceDrivePub = rospy.Publisher('Forklift/DistanceDrive/Read', DD, queue_size=1, latch=True)
                
                #Deklaracje subskrybowanych topicow ROS
                self.Forklift_states_write_sub = rospy.Subscriber('Forklift/state/workstates/Requested', WS, self.workstates_received)
                self.servo_direction_sub = rospy.Subscriber('PLC/write/ServoDirection', Int64, self.servo_direction_read)
                self.servo_value_sub = rospy.Subscriber('PLC/write/ServoAngle', Int64, self.servo_value_read)
                # self.servo_direction_sub = rospy.Subscriber('PLC/write/servo_direction', Int64, self.servo_direction_read)
                # self.servo_value_sub = rospy.Subscriber('PLC/write/servo_value', Int64, self.servo_value_read)
                self.user_logged_sub = rospy.Subscriber('Forklift/state/user/login_status', Bool, self.user_login_read)
                # self.PWM_sub = rospy.Subscriber('PLC/write/command_pwm_value', Int64, self.command_pwm_read)
                # self.PWM_dir_sub = rospy.Subscriber('PLC/write/command_pwm_direction', Int64, self.command_pwm_direction)
                # self.servo_power_sub = rospy.Subscriber('PLC/write/servo_power', Int64, self.servo_power_read)
                self.PWM_sub = rospy.Subscriber('PLC/write/CurtisPWM', Int64, self.command_pwm_read)
                self.PWM_dir_sub = rospy.Subscriber('PLC/write/CurtisDirection', Int64, self.command_pwm_direction)
                self.servo_power_sub = rospy.Subscriber('PLC/write/ServoPower', Int64, self.servo_power_read)
                self.forks_command_sub = rospy.Subscriber('PLC/write/forks_command', Int64, self.forks_command_read)
                self.DistanceDriveCommandsSub = rospy.Subscriber('Forklift/DistanceDrive/Write', DD, self.DistanceDriveCallback)
                self.ScangridsDataInSub = rospy.Subscriber('Forklift/Scangrids/DataIn', Scangrids, self.ScangridsDataInCallback)
            except(rospy.ServiceException, rospy.ROSException, SystemExit) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
            #Wyzwolenie komunikacji
            self.Communication()
    def ScangridsDataInCallback(self, msg):
        self.ScangridsDataIn = msg
    def DistanceDriveCallback(self, msg):
        self.DistanceSend = msg
    def user_login_read(self, msg):
        self.OperatorLoggedIn = msg.data          
    def command_pwm_read(self, msg):
        #Odczyt zadanej wartosci PWM do napedu wozka
        self.CurtisPWM = msg.data
    def command_pwm_direction(self, msg):
        #Odczyt zadanego kierunku ruchu do napedu wozka
        self.CurtisDirection = msg.data
    def servo_direction_read(self, msg):
        #Odczyt zadanego kierunku skretu (serwonaped)
        self.ServoDirection = msg.data
    def servo_value_read(self, msg):
        #Odczyt zadanego kata skretu (serwonaped)
        self.ServoAngle = msg.data
    def servo_power_read(self, msg):
        #Odczyt zadanego stanu serwonapedu ( ON/OFF )
        self.ServoPower = msg.data
    def workstates_received(self, msg):
        #Odczyt zadanego stanu pracy
        self.WorkstatesFromROS = msg 
    def ReadList(self):
        #Sortowanie i publikowanie do topicow ROS danych z odczytanej tabeli z PLC
        self.mutex.acquire()
        self.ReadDataTable = self.DeltaPLC.read_holding_registers(200, 99) # Odczyt 99 rejestrow z PLC
        self.mutex.release()
        if self.ReadDataTable != None:
            print(self.ReadDataTable[5])
            self.ForkHeightPub.publish(self.ReadDataTable[0])
            self.CargoWeightPub.publish(self.ReadDataTable[1])
            self.TiltAxis1Pub.publish(self.ReadDataTable[2])
            self.TiltAxis2Pub.publish(self.ReadDataTable[3])
            self.BatteryVoltagePub.publish(self.ReadDataTable[4])
            self.EncoderSpeedPub.publish(self.ReadDataTable[5])
            self.EncoderDirectionPub.publish(self.ReadDataTable[6])
            self.ForksHeightLimiterStatusPub.publish(self.ReadDataTable[7])
            self.ServoActualDirectionPub.publish(self.ReadDataTable[8])
            self.ServoActualAnglePub.publish(self.ReadDataTable[9])
            self.DistanceReadPub.publish(self.ReadDataTable[10])
            # self.current_work_state_pub.publish(self.ROS_read[10])
            return True
        else:
            self.ConnectionPLC = False
            return False
    def WriteList(self):
        #Sortowanie i zapisywanie danych otrzymanych do zapisu do PLC w liste
        
        self.WriteDataTable[0] = self.ServoDirection
        self.WriteDataTable[1] = self.ServoAngle
        self.WriteDataTable[2] = self.ServoPower
        self.WriteDataTable[3] = self.GiveWorkstate 
        self.WriteDataTable[4] = self.CurtisDirection 
        self.WriteDataTable[5] = self.CurtisPWM
        self.WriteDataTable[6] = self.ForksCommand
        self.WriteDataTable[7] = int(self.DistanceSend.RequestedDistance)
        self.WriteDataTable[98] = self.Watchdog
    def IO_Write(self):
        self.SignalsInTable[0] = self.ScangridsActivator
        #Petla przekazania stanow pracy na liste zapisu do PLC
        rospy.loginfo(self.WorkstatesReadedPLC)
        self.SignalsInTable[8] = self.WorkstatesFromROS.AutoMode
        self.SignalsInTable[9] = self.WorkstatesFromROS.IniDiagCompleted
        self.SignalsInTable[10] = self.WorkstatesFromROS.StartNavride
        self.SignalsInTable[11] = self.WorkstatesFromROS.FinishNavride
        self.SignalsInTable[12] = self.WorkstatesFromROS.StartCharging
        self.SignalsInTable[13] = self.WorkstatesFromROS.FinishCharging
        self.SignalsInTable[14] = self.WorkstatesFromROS.StartMagazineGetCargo
        self.SignalsInTable[15] = self.WorkstatesFromROS.FinishMagazineGetCargo
        self.SignalsInTable[16] = self.WorkstatesFromROS.StartMagazineLeaveCargo
        self.SignalsInTable[17] = self.WorkstatesFromROS.FinishMagazineLeaveCargo
        self.SignalsInTable[18] = self.WorkstatesFromROS.StartNestGetCargo
        self.SignalsInTable[19] = self.WorkstatesFromROS.FinishNestGetCargo
        self.SignalsInTable[20] = self.WorkstatesFromROS.StartNestLeaveCargo
        self.SignalsInTable[21] = self.WorkstatesFromROS.FinishNestLeaveCargo
        self.SignalsInTable[24] = self.OperatorLoggedIn
        self.SignalsInTable[25] = self.DistanceSend.EnableDistanceDrive
        self.SignalsInTable[26] = self.DistanceSend.ResetDistanceDrive
        self.SignalsInTable[27] = self.DistanceSend.CancelDistanceDrive
        self.SignalsInTable[28] = self.ScangridsDataIn.Steering.ActivateLeftPaletteDetection
        self.SignalsInTable[29] = self.ScangridsDataIn.Steering.ActivateRightPaletteDetection
        self.SignalsInTable[30] = self.ScangridsDataIn.Steering.ActivateAllZones
        for i in range (0, len(self.SignalsInTable)):
            if self.SignalsInTable[i] == None:
                self.SignalsInTable[i] = False  
        rospy.loginfo (self.SignalsInTable)
        self.DeltaPLC.write_multiple_coils(41120, self.SignalsInTable) # Zapis sygnalow w PLC ( limit 80 )
    def IO_Read(self):
        self.SignalsOutTable = self.DeltaPLC.read_coils(41200, 80)
        if self.SignalsOutTable != None:
            rospy.loginfo (self.SignalsOutTable)
            self.WorkstatesReadedPLC.S0_1 = self.SignalsOutTable[8]
            self.WorkstatesReadedPLC.S0_2 = self.SignalsOutTable[9]
            self.WorkstatesReadedPLC.S0_3 = self.SignalsOutTable[10]
            self.WorkstatesReadedPLC.S1 = self.SignalsOutTable[11]
            self.WorkstatesReadedPLC.S2 = self.SignalsOutTable[12]
            self.WorkstatesReadedPLC.S3 = self.SignalsOutTable[13]
            self.WorkstatesReadedPLC.S4 = self.SignalsOutTable[14]
            self.WorkstatesReadedPLC.S4_0 = self.SignalsOutTable[15]
            self.WorkstatesReadedPLC.S4_1 = self.SignalsOutTable[16]
            self.WorkstatesReadedPLC.S4_2 = self.SignalsOutTable[17]
            self.WorkstatesReadedPLC.S4_3 = self.SignalsOutTable[18]
            self.WorkstatesReadedPLC.S4_4 = self.SignalsOutTable[19]
            self.WorkstatesReadedPLC.S4_5 = self.SignalsOutTable[20]
            self.WorkstatesReadedPLC.S4_6 = self.SignalsOutTable[21]
            self.DistanceRead.BasePositionSaved = self.SignalsOutTable[22]
            self.DistanceRead.PositionReached = self.SignalsOutTable[23]
            self.ScangridsDataOut.LeftScannerStatus.SafetyOutput = self.SignalsOutTable[32]
            self.ScangridsDataOut.LeftScannerStatus.ProtectFieldStatus = self.SignalsOutTable[33]
            self.ScangridsDataOut.LeftScannerStatus.WorkStatus = self.SignalsOutTable[34]
            self.ScangridsDataOut.LeftScannerStatus.WarningFieldStatus = self.SignalsOutTable[40]
            self.ScangridsDataOut.LeftScannerStatus.ContaminationWarning = self.SignalsOutTable[41]
            self.ScangridsDataOut.LeftScannerStatus.ContaminationError = self.SignalsOutTable[42]
            self.ScangridsDataOut.LeftScannerStatus.MonitoringCaseSwitchInputStatus = not self.SignalsOutTable[43]
            self.ScangridsDataOut.LeftScannerStatus.MonitoringCaseSwitchCANInputStatus = not self.SignalsOutTable[44]
            self.ScangridsDataOut.LeftScannerStatus.VoltageError = self.SignalsOutTable[45]
            self.ScangridsDataOut.LeftScannerStatus.ResistanceToExternalLightError = self.SignalsOutTable[46]
            self.ScangridsDataOut.LeftScannerStatus.SleepModeStatus = self.SignalsOutTable[47]
            self.ScangridsDataOut.RightScannerStatus.SafetyOutput = self.SignalsOutTable[48]
            self.ScangridsDataOut.RightScannerStatus.ProtectFieldStatus = self.SignalsOutTable[49]
            self.ScangridsDataOut.RightScannerStatus.WorkStatus = self.SignalsOutTable[50]
            self.ScangridsDataOut.RightScannerStatus.WarningFieldStatus = self.SignalsOutTable[56]
            self.ScangridsDataOut.RightScannerStatus.ContaminationWarning = self.SignalsOutTable[57]
            self.ScangridsDataOut.RightScannerStatus.ContaminationError = self.SignalsOutTable[58]
            self.ScangridsDataOut.RightScannerStatus.MonitoringCaseSwitchInputStatus = not self.SignalsOutTable[59]
            self.ScangridsDataOut.RightScannerStatus.MonitoringCaseSwitchCANInputStatus = not self.SignalsOutTable[60]
            self.ScangridsDataOut.RightScannerStatus.VoltageError = self.SignalsOutTable[61]
            self.ScangridsDataOut.RightScannerStatus.ResistanceToExternalLightError = self.SignalsOutTable[62]
            self.ScangridsDataOut.RightScannerStatus.SleepModeStatus = self.SignalsOutTable[63]
            self.DistanceDrivePub.publish(self.DistanceRead)
            rospy.loginfo(self.DistanceRead)
            self.ActiveWorkstatePub.publish(self.WorkstatesReadedPLC)
            self.ReinitializeAutoModePub.publish(self.OperatorResetAutoMode)
            self.OperatorResetAutoMode = self.SignalsOutTable[24]
        else:
            rospy.loginfo('Signals_Out none type')
    def ErrorList(self):
        #Odczyt wewnetrznych bledow w PLC i przekazanie ich w topic log_saver
        module_str = ''
        error_code = ''
        self.Errors = self.DeltaPLC.read_holding_registers(500, 99) # Odczyt tablicy kodow bledow
        if self.Errors != None and self.ConnectionPLC:
                #Podczialy bledow na moduly, przypisanie wagi bledu oraz dodanie nazwy modulu i kodu bledu do zapisu
            if self.Errors[0] != 0:
                module_str = 'Scagrid left error code:'
                error_code = str(self.Errors[0])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                if self.GiveWorkstate == 3 :
                    self.LogLEvel = 5
                else:
                    self.LogLEvel = 3
                self.LogLEvelPub.publish(self.LogLEvel)
            if self.Errors[1] != 0:
                module_str = 'Scagrid right error code:'
                error_code = str(self.Errors[1])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                if self.GiveWorkstate == 3 :
                    self.LogLEvel = 5
                else:
                    self.LogLEvel = 3
                self.LogLEvelPub.publish(self.LogLEvel)
            if self.Errors[2] != 0:
                module_str = 'Pressure sensor error code:'
                error_code = str(self.Errors[2])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                self.LogLEvel = 4
                self.LogLEvelPub.publish(self.LogLEvel)
            if self.Errors[3] != 0:
                module_str = 'Forks height sensor error code:'
                error_code = str(self.Errors[3])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                self.LogLEvel = 4
                self.LogLEvelPub.publish(self.LogLEvel)
            if self.Errors[4] != 0:
                module_str = 'Tilt sensor axis 1 error code:'
                error_code = str(self.Errors[4])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                self.LogLEvel = 4
                self.LogLEvelPub.publish(self.LogLEvel)
            if self.Errors[5] != 0:
                module_str = 'Tilt sensor axis 2 error code:'
                error_code = str(self.Errors[5])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                self.LogLEvel = 4
                self.LogLEvelPub.publish(self.LogLEvel)
            if self.Errors[6] != 0:
                module_str = 'Battery read error code:'
                error_code = str(self.Errors[6])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                self.LogLEvel = 5
                self.LogLEvelPub.publish(self.LogLEvel)
            if self.Errors[8] != 0:
                module_str = 'Curtis speed write error code:'
                error_code = str(self.Errors[8])
                self.LogMessage = module_str + error_code
                self.LogMessagePub.publish(self.LogMessage)
                self.LogLEvel = 4
                self.LogLEvelPub.publish(self.LogLEvel)
            else:
                self.LogLEvel = 0
                self.LogMessage = ''
                error_code = ''
                module_str = ''
                
        else:
            self.ConnectionPLC = False
    def Scangrids(self):
        #Odczyt danych otrzymanych z Scangrid2
        RightScanner = self.DeltaPLC.read_holding_registers(600, 32)
        LeftScanner = self.DeltaPLC.read_holding_registers(650, 32)
        if self.ScangridsDataOut.LeftScanner == None:
            self.LogMessage = 'PLC Communication: Error in readings from Scangrid left'
            self.LogLEvel = 4
            self.LogLEvelPub.publish(self.LogLEvel)
            self.LogMessagePub.publish(self.LogMessage)
            self.ConnectionPLC = False
        if self.ScangridsDataOut.RightScanner == None:
            self.LogMessage = 'PLC Communication: Error in readings from Scangrid right'
            self.LogLEvel = 4
            self.LogLEvelPub.publish(self.LogLEvel)
            self.ConnectionPLC = False
            self.LogMessagePub.publish(self.LogMessage)
        if not self.ScangridsDataIn.Steering.ActivateAllZones and not self.ScangridsDataIn.Steering.ActivateLeftPaletteDetection and not self.ScangridsDataIn.Steering.ActivateRightPaletteDetection:
            for i in range(0, 32):
                LeftScanner[i] = 0
                RightScanner[i] = 0

        self.ScangridsDataOut.LeftScanner.Range0 = LeftScanner[0]
        self.ScangridsDataOut.LeftScanner.Range1 = LeftScanner[1]
        self.ScangridsDataOut.LeftScanner.Range2 = LeftScanner[2]
        self.ScangridsDataOut.LeftScanner.Range3 = LeftScanner[3]
        self.ScangridsDataOut.LeftScanner.Range4 = LeftScanner[4]
        self.ScangridsDataOut.LeftScanner.Range5 = LeftScanner[5]
        self.ScangridsDataOut.LeftScanner.Range6 = LeftScanner[6]
        self.ScangridsDataOut.LeftScanner.Range7 = LeftScanner[7]
        self.ScangridsDataOut.LeftScanner.Range8 = LeftScanner[8]
        self.ScangridsDataOut.LeftScanner.Range9 = LeftScanner[9]
        self.ScangridsDataOut.LeftScanner.Range10 = LeftScanner[10]
        self.ScangridsDataOut.LeftScanner.Range11 = LeftScanner[11]
        self.ScangridsDataOut.LeftScanner.Range12 = LeftScanner[12]
        self.ScangridsDataOut.LeftScanner.Range13 = LeftScanner[13]
        self.ScangridsDataOut.LeftScanner.Range14 = LeftScanner[14]
        self.ScangridsDataOut.LeftScanner.Range15 = LeftScanner[15]
        self.ScangridsDataOut.LeftScanner.Range16 = LeftScanner[16]
        self.ScangridsDataOut.LeftScanner.Range17 = LeftScanner[17]
        self.ScangridsDataOut.LeftScanner.Range18 = LeftScanner[18]
        self.ScangridsDataOut.LeftScanner.Range19 = LeftScanner[19]
        self.ScangridsDataOut.LeftScanner.Range20 = LeftScanner[20]
        self.ScangridsDataOut.LeftScanner.Range21 = LeftScanner[21]
        self.ScangridsDataOut.LeftScanner.Range22 = LeftScanner[22]
        self.ScangridsDataOut.LeftScanner.Range23 = LeftScanner[23]
        self.ScangridsDataOut.LeftScanner.Range24 = LeftScanner[24]
        self.ScangridsDataOut.LeftScanner.Range25 = LeftScanner[25]
        self.ScangridsDataOut.LeftScanner.Range26 = LeftScanner[26]
        self.ScangridsDataOut.LeftScanner.Range27 = LeftScanner[27]
        self.ScangridsDataOut.LeftScanner.Range28 = LeftScanner[28]
        self.ScangridsDataOut.LeftScanner.Range29 = LeftScanner[29]
        self.ScangridsDataOut.LeftScanner.Range30 = LeftScanner[30]
        self.ScangridsDataOut.LeftScanner.Range31 = LeftScanner[31]
        self.ScangridsDataOut.RightScanner.Range0 = RightScanner[0]
        self.ScangridsDataOut.RightScanner.Range1 = RightScanner[1]
        self.ScangridsDataOut.RightScanner.Range2 = RightScanner[2]
        self.ScangridsDataOut.RightScanner.Range3 = RightScanner[3]
        self.ScangridsDataOut.RightScanner.Range4 = RightScanner[4]
        self.ScangridsDataOut.RightScanner.Range5 = RightScanner[5]
        self.ScangridsDataOut.RightScanner.Range6 = RightScanner[6]
        self.ScangridsDataOut.RightScanner.Range7 = RightScanner[7]
        self.ScangridsDataOut.RightScanner.Range8 = RightScanner[8]
        self.ScangridsDataOut.RightScanner.Range9 = RightScanner[9]
        self.ScangridsDataOut.RightScanner.Range10 = RightScanner[10]
        self.ScangridsDataOut.RightScanner.Range11 = RightScanner[11]
        self.ScangridsDataOut.RightScanner.Range12 = RightScanner[12]
        self.ScangridsDataOut.RightScanner.Range13 = RightScanner[13]
        self.ScangridsDataOut.RightScanner.Range14 = RightScanner[14]
        self.ScangridsDataOut.RightScanner.Range15 = RightScanner[15]
        self.ScangridsDataOut.RightScanner.Range16 = RightScanner[16]
        self.ScangridsDataOut.RightScanner.Range17 = RightScanner[17]
        self.ScangridsDataOut.RightScanner.Range18 = RightScanner[18]
        self.ScangridsDataOut.RightScanner.Range19 = RightScanner[19]
        self.ScangridsDataOut.RightScanner.Range20 = RightScanner[20]
        self.ScangridsDataOut.RightScanner.Range21 = RightScanner[21]
        self.ScangridsDataOut.RightScanner.Range22 = RightScanner[22]
        self.ScangridsDataOut.RightScanner.Range23 = RightScanner[23]
        self.ScangridsDataOut.RightScanner.Range24 = RightScanner[24]
        self.ScangridsDataOut.RightScanner.Range25 = RightScanner[25]
        self.ScangridsDataOut.RightScanner.Range26 = RightScanner[26]
        self.ScangridsDataOut.RightScanner.Range27 = RightScanner[27]
        self.ScangridsDataOut.RightScanner.Range28 = RightScanner[28]
        self.ScangridsDataOut.RightScanner.Range29 = RightScanner[29]
        self.ScangridsDataOut.RightScanner.Range30 = RightScanner[30]
        self.ScangridsDataOut.RightScanner.Range31 = RightScanner[31]

        self.ScangridsDataOutPub.publish(self.ScangridsDataOut)
    def Plc_connect(self):
        self.DeltaPLC.close()
        self.DeltaPLC = None
        self.DeltaPLC = client.ModbusClient("192.168.1.4", 502, auto_close=True, auto_open=True)
        rospy.loginfo('+++++++++<<<<<< RECONNECTION LOOP >>>>>>++++++++')            
    def watchdog(self):
        self.WatchdogOld = self.Watchdog
        if self.WatchdogOld == 1:
            self.Watchdog = 2
        elif self.WatchdogOld == 2:
            self.Watchdog = 1
    def forks_command_read(self, msg):
        self.ForksCommand = msg.data
    def Communication(self):
        rospy.loginfo('kurde') 
        self.ReadList() #Wywolanie sortowania odczytanych sygnalow
        self.WriteList() #wywolanie sortowania danych z ROS do zapisu
        self.watchdog()
        self.mutex.acquire()
        info = self.DeltaPLC.write_multiple_registers(100, self.WriteDataTable) # Zapis rejestrow PLC ( limit 99 )
        self.mutex.release()
        if info == None and self.ConnectionPLC:
            self.LogMessage = 'PLC Communication: Error in writing PLC Datatable.'
            self.LogLEvel = 5
            self.LogLEvelPub.publish(self.LogLEvel)
            self.LogMessagePub.publish(self.LogMessage)
            self.ConnectionPLC = False
        self.IO_Read() #Wywoalnie sortowania sygnalow z ROS do zapisu 
        self.IO_Write()
        if info == None and self.ConnectionPLC:
            self.LogMessage = 'PLC Communication: Error in writing IO to PLC.'
            self.LogLEvel = 5
            self.LogLEvelPub.publish(self.LogLEvel)
            self.LogMessagePub.publish(self.LogMessage)
            self.ConnectionPLC = False
        if self.Errors != None:
            self.ErrorList()
        
        #czyszczenie list
        if self.ReadDataTable != None:
            self.ReadDataTable.clear()
        if self.VirtualIOTable != None:
            self.VirtualIOTable.clear()
        self.Clear() 
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