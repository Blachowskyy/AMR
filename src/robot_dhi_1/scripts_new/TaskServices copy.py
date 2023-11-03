#!/usr/bin/env python3
import rospy
import os
import csv
import asyncio
from time import sleep as s
from robot_dhi_1.msg import FleetManagerTaskDataIn as FMSTaskIn, FleetManagerTaskDataOut as FMSTaskOut
from robot_dhi_1.msg import FleetManagerCommandsIn as CommandsIn, FleetManagerCommandsOut as CommandsOut
from std_msgs.msg import String
from actionlib_msgs.msg import GoalStatusArray, GoalStatus

class TaskServices:
    def __init__(self):
        # Deklaracje globalnych zmiennych uzywanych w modulach programu
        self.taskReceived = FMSTaskIn()      #Otrzymane zadanie
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
                self.activeTaskPub = rospy.Publisher('Forklift/state/WMS/activeTask', FMSTaskOut, queue_size=1)
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
        print(self.commands)
    def receivedTaskCallback(self, msg):
        rospy.loginfo("TASK CALLBACK")
        self.taskReceived = msg
        taskIdNow = ''
        taskIdOld = ''
        taskIdNow = self.taskReceived.TaskID
        taskIdOld = self.taskReceivedOld.TaskID
        if taskIdNow != taskIdOld:
            rospy.loginfo("New task arrived")
            self.taskQueueList.append(self.taskReceived)
            self.taskQueueListCount = len(self.taskQueueList)
            self.taskQueueToFMS = self.taskQueueToFMS + str(self.taskReceived)  + '#'
            self.taskQueuePub.publish(self.taskQueueToFMS)
            # print(self.taskQueueToFMS)
            self.taskReceivedOld = self.taskReceived
    #Archiwizacja zakonczonego badz anulowanego zadania do pliku csv
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
        self.taskQueueList.sort(key=lambda task: (task.ImportanceLevel, task.TaskDate))
        if len(self.taskQueueList) > 0:
            self.taskQueueToFMS = ''
            for task in self.taskQueueList:
                self.taskQueueToFMS = self.taskQueueToFMS + str(task)  + '#'    
            self.taskQueuePub.publish(self.taskQueueToFMS)
            # print(self.taskQueueToFMS)
            # print(self.commands.cancelLastTask)
            #Wybor zadania na aktywne jesli zadne nie jest realizowane
            if not self.activeTask.isRunning and not self.commands.cancelLastTask:
                self.activeTask = self.taskQueueList[0]
                self.activeTask.isRunning = True
                self.activeTaskPub.publish(self.activeTask)
            if self.commands.cancelLastTask:
                rospy.loginfo("Task canceling function")
                if self.taskQueueListCount > 2:
                    self.taskQueueList.remove()
                    self.taskQueueListCount = len(self.taskQueueList)
                    self.activeTask = self.taskQueueList[0]
                    self.activeTask.isRunning = True
                    self.activeTaskPub.publish(self.activeTask)
                    self.confirmCommands.confirmCancelLastTask = True
                    self.commandFMSPub.publish(self.confirmCommands)
                    while self.commands.confirmCancelLastTask:
                        s(0.1)
                        if not self.commands.cancelLastTask:
                            break
                if self.taskQueueListCount < 2 and self.taskQueueListCount >=1:
                    self.taskQueueList.remove()
                    self.taskQueueListCount = len(self.taskQueueList)
                    self.activeTask = FMSTaskOut()
                    self.activeTaskPub.publish(self.activeTask)
                    self.confirmCommands.confirmCancelLastTask = True
                    self.commandFMSPub.publish(self.confirmCommands)
                    while self.commands.confirmCancelLastTask:
                        s(0.1)
                        if not self.commands.cancelLastTask:
                            break
                if self.taskQueueListCount < 1:
                    self.confirmCommands.confirmCancelLastTask = True
                    self.commandFMSPub.publish(self.confirmCommands)
                    while self.commands.confirmCancelLastTask:
                        s(0.1)
                        if not self.commands.cancelLastTask:
                            break
                    # rospy.loginfo("Proba usuniecia pustej listy zadan !")
            #Petla do momentu zakonczenia zadania lub anulowania zadania
            while self.activeTask.isRunning:
                
                if self.commands.cancelLastTask:
                    self.activeTask.confirmCancelingActualTask = True
                    self.taskToArchive = self.activeTask
                    self.taskArchiving()
                    self.activeTaskPub.publish(self.activeTask)
                    break;
                if self.activeTask.isDone:
                    self.activeTask.isDone = True
                    self.taskToArchive = self.activeTask
                    self.taskArchiving()
                    self.activeTaskPub.publish(self.activeTask)
                    break;
                
    async def GoalCheck(self):
        while True:  # Pętla zewnętrzna
            if not self.activeTask.isRunning:
                await asyncio.sleep(0.1)  # Opóźnienie, aby uniknąć obciążenia CPU
                continue
            rospy.loginfo('GoalCheck active')
            if self.activeTask.TaskType == 1:
                rospy.loginfo('GoalCheck taskType 1 - navride')
                while not (self.moveBaseResult == 3 and self.activeTask.cancelActualTask):
                    await asyncio.sleep(0.1)  # Opóźnienie, aby uniknąć obciążenia CPU
                if self.moveBaseResult == 3:
                    self.activeTask.isDone = True
                    rospy.loginfo('GoalCheck: Goal achieved now.')
                    break  # Przerwij pętlę zewnętrzną, jeżeli zadanie jest zakończone
                if self.activeTask.cancelActualTask:
                    self.activeTask.isDone = False
                    rospy.loginfo('GoalCheck: Goal was aborted.')
                    break

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
