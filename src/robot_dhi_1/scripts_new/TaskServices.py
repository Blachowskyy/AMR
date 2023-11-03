#!/usr/bin/env python3
import rospy
import os
import csv
import datetime
import asyncio
from time import sleep as s
from robot_dhi_1.msg import FleetManagerTaskDataIn as FMSTaskIn, FleetManagerTaskDataOut as FMSTaskOut
from robot_dhi_1.msg import FleetManagerCommandsIn as CommandsIn, FleetManagerCommandsOut as CommandsOut
from std_msgs.msg import String
from actionlib_msgs.msg import GoalStatusArray, GoalStatus

class TaskServices:
    def __init__(self):
        # Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.taskReceived = FMSTaskIn() 
        self.TaskReceivedConverter = FMSTaskOut()#Otrzymane zadanie
        self.taskStatus = FMSTaskOut()
        self.taskQueueList = list()  
        self.taskQueueToFMS = ''#Lista wszystkich zadan
        self.activeTask = FMSTaskOut()        #Zadanie aktywne
        self.taskToArchive = FMSTaskOut()     #Zadanie do archiwizacji do pliku
        self.taskReceivedOld = FMSTaskIn()   #ostatnie otrzymane zadanie
        self.taskToArchive.CurrentTaskID = 0   
        self.taskQueueListCount = 0#Ustawienie taskid na 0 w celu kontroli archiwizacji
        self.moveBaseResults = GoalStatusArray()
        self.commands = CommandsIn()
        self.confirmCommands = CommandsOut()
        self.moveBaseResult = 0
        self.startup = True
        # asyncio.run(self.GoalCheck())
        while not rospy.is_shutdown():
            try:
                # Deklaracje subskrybcji wiadomosci z systemu ROS
                self.receivedTaskSub = rospy.Subscriber('Forklift/state/WMS/receivedTask', FMSTaskIn, self.receivedTaskCallback)
                # self.goalReachedSub = rospy.Subscriber('/move_base/status', GoalStatusArray, self.moveBaseResultCallback)
                self.commandFMSSub = rospy.Subscriber('Forklift/state/WMS/receivedCommand', CommandsIn, self.commandsCallback )
                self.commandFMSPub = rospy.Publisher('Forklift/state/Wms/confirmCommand', CommandsOut, queue_size=1)
                self.activeTaskPub = rospy.Publisher('Forklift/state/WMS/activeTask', FMSTaskOut, queue_size=1, latch=True)
                self.taskQueuePub = rospy.Publisher('Forklift/state/WMS/queuedTasks', String, queue_size=1, latch=True)
            except (rospy.ServiceException, rospy.ROSException) as e:
                rospy.logerr("connect/subscribers/publishers: %s" % e)
            self.TaskQueue() #Metoda glowna 
    # def moveBaseResultCallback(self, msg):    
    #     self.moveBaseResults = msg.status_list
    #     self.moveBaseResult = self.moveBaseResults[0].status
    #     print(self.moveBaseResult)  
    # Odczyt subscriberow
    def commandsCallback(self, msg):
        self.commands = msg  
    def receivedTaskCallback(self, msg):
        self.taskReceived = msg
        taskIdNow = ''
        taskIdOld = ''
        taskIdNow = self.taskReceived.TaskID
        taskIdOld = self.taskReceivedOld.TaskID
        rospy.loginfo_once(taskIdNow)
        rospy.loginfo_once(taskIdOld)
        if taskIdNow != taskIdOld:
            rospy.loginfo("New task arrived")
            self.ReceivedTaskConverter()
            self.TaskReceivedConverter.CurrentTaskReceivedDate = str(datetime.datetime.now())
            self.taskQueueList.append(self.TaskReceivedConverter)
            self.taskQueueListCount = len(self.taskQueueList)
            self.taskQueueToFMS = self.taskQueueToFMS + str(self.taskReceived)  + '#'
            self.taskQueuePub.publish(self.taskQueueToFMS)
            # print(self.taskQueueToFMS)
            self.taskReceivedOld = self.taskReceived
    #Archiwizacja zakonczonego badz anulowanego zadania do pliku csv
    def ReceivedTaskConverter(self):
        self.TaskReceivedConverter.CurrentTaskCoordinatesX = self.taskReceived.CoordinatesX
        self.TaskReceivedConverter.CurrentTaskCoordinatesY = self.taskReceived.CoordinatesY
        self.TaskReceivedConverter.CurrentTaskCoordinatesTetha = self.taskReceived.CoordinatesTetha
        self.TaskReceivedConverter.CurrentTaskID = self.taskReceived.TaskID
        self.TaskReceivedConverter.CurrentTaskReceivedDate = self.taskReceivedOld.TaskDate
        self.TaskReceivedConverter.CurrentTaskType = self.taskReceived.TaskType
        self.TaskReceivedConverter.CurrentTaskImportanceLevel = self.taskReceived.ImportanceLevel
        self.TaskReceivedConverter.CurrentTaskIsInQueue = True
        self.TaskReceivedConverter.CurrentTaskIsInProgress = False
        self.TaskReceivedConverter.CurrentTaskIsDone = False
    def taskArchiving(self):
        if self.taskToArchive.CurrentTaskID != 0:                              #kontrola zapisu
                archiveFolder = "data"                                  #Deklaracja nazwy folderu
                if not os.path.exists(archiveFolder):                   #Utworzenie folderu gdy nie istnieje
                    os.makedirs(archiveFolder)                          
                fileName = os.path.join(archiveFolder, "taskArchive.csv")    #Deklaracja pliku do zapisu
                with open(fileName, mode="a", newline="") as file:      #Zapis w trybie dodania wiersza (utworzy plik, jesli nie istnieje)
                    writer = csv.writer(file)                            #deklaracja metody zapisu do pliku
                    writer.writerow([self.taskToArchive])               #Zapisanie zmiennej do pliku
                    self.taskToArchive = FMSTaskOut()                 #Wyzerowanie zmiennej po zapisie
                    self.taskToArchive.CurrentTaskID = 0                       #Przywrocenie liczby kontrolnej
    def TaskQueue(self):
        os.system('clear')
        # Sortowanie listy taskQueueList na podstawie pola TaskDate i ImportanceLevel
        self.taskQueueList.sort(key=lambda task: (task.CurrentTaskImportanceLevel, task.CurrentTaskReceivedDate))
        if len(self.taskQueueList) > 0:
            self.taskQueueToFMS = ''
            for task in self.taskQueueList:
                self.taskQueueToFMS = self.taskQueueToFMS + str(task)  + '#'    
            self.taskQueuePub.publish(self.taskQueueToFMS)
            print(self.taskQueueToFMS)
            print(self.commands.CancelLastTask)
            #Wybor zadania na aktywne jesli zadne nie jest realizowane
            if not self.activeTask.CurrentTaskIsDone and not self.commands.CancelLastTask:
                self.activeTask = self.taskQueueList[0]
                self.activeTask.CurrentTaskIsInProgress = True
                self.activeTaskPub.publish(self.activeTask)
            if self.commands.CancelLastTask:
                rospy.loginfo("Task canceling function")
                if self.taskQueueListCount > 2:
                    self.taskQueueList.remove()
                    self.taskQueueListCount = len(self.taskQueueList)
                    self.activeTask = self.taskQueueList[0]
                    self.activeTask.CurrentTaskIsInProgress = False
                    self.activeTaskPub.publish(self.activeTask)
                    self.confirmCommands.ConfirmCancelLastTask = True
                    self.commandFMSPub.publish(self.confirmCommands)
                    while self.commands.CancelLastTask:
                        s(0.1)
                        if not self.commands.CancelLastTask:
                            break
                if self.taskQueueListCount < 2 and self.taskQueueListCount >=1:
                    self.taskQueueList.remove()
                    self.taskQueueListCount = len(self.taskQueueList)
                    self.activeTask = FMSTaskOut()
                    self.activeTaskPub.publish(self.activeTask)
                    self.confirmCommands.ConfirmCancelLastTask = True
                    self.commandFMSPub.publish(self.confirmCommands)
                    while self.commands.CancelLastTask:
                        s(0.1)
                        if not self.commands.CancelLastTask:
                            break
                if self.taskQueueListCount < 1:
                    self.confirmCommands.ConfirmCancelLastTask = True
                    self.commandFMSPub.publish(self.confirmCommands)
                    while self.commands.CancelLastTask:
                        s(0.1)
                        if not self.commands.CancelLastTask:
                            break
                    # rospy.loginfo("Proba usuniecia pustej listy zadan !")
            #Petla do momentu zakonczenia zadania lub anulowania zadania
            while self.activeTask.CurrentTaskIsInProgress:
                
                if self.commands.CancelLastTask:
                    self.confirmCommands.ConfirmCancelLastTask = True
                    self.taskToArchive = self.activeTask
                    self.taskArchiving()
                    self.activeTaskPub.publish(self.activeTask)
                    break;
                if self.activeTask.CurrentTaskIsDone:
                    
                    self.taskToArchive = self.activeTask
                    self.taskArchiving()
                    self.activeTaskPub.publish(self.activeTask)
                    break;
                
    # async def GoalCheck(self):
    #     while True:  # Pętla zewnętrzna
    #         if not self.activeTask.isRunning:
    #             await asyncio.sleep(0.1)  # Opóźnienie, aby uniknąć obciążenia CPU
    #             continue
    #         rospy.loginfo('GoalCheck active')
    #         if self.activeTask.TaskType == 1:
    #             rospy.loginfo('GoalCheck taskType 1 - navride')
    #             while not (self.moveBaseResult == 3 and self.activeTask.cancelActualTask):
    #                 await asyncio.sleep(0.1)  # Opóźnienie, aby uniknąć obciążenia CPU
    #             if self.moveBaseResult == 3:
    #                 self.activeTask.isDone = True
    #                 rospy.loginfo('GoalCheck: Goal achieved now.')
    #                 break  # Przerwij pętlę zewnętrzną, jeżeli zadanie jest zakończone
    #             if self.activeTask.cancelActualTask:
    #                 self.activeTask.isDone = False
    #                 rospy.loginfo('GoalCheck: Goal was aborted.')
    #                 break

if __name__ == '__main__':
    try:    
        rospy.init_node('TaskService')
        taskServices = TaskServices()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
        rospy.spin()
        
    except (rospy.ServiceException, rospy.ROSException) as e:
        rospy.logerr("Main call failed: %s" % e)
    
    finally:
        rospy.loginfo('++++++++++++++++++ OUT ++++++++++++++++++')
