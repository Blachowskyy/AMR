#!/usr/bin/env python3
import rospy
import os
import json
import asyncio
from std_msgs.msg import Bool
from robot_dhi_1.msg import TEBConfigMessages as TEB
from dynamic_reconfigure.client import Client
from time import sleep
class ParametersService:
    def __init__(self):
        rospy.loginfo('Initializing parameters service')
        #Zmienne inicjalizujące załadowanie pliku oraz jego miejsce/nazwę
        self.LoadSettingsFromFile = True
        self.FileDirectory = "src/robot_dhi_1/settings"
        self.FileName = "TEBsettings.json"
        #Zmienne, na które zostaną przypisane otrzymane wartości ustawień
        self.MaxAccelerationX = 0.0
        self.MaxAccelerationTheta = 0.0
        self.MaxSpeedX = 0.0
        self.MaxSpeedBackwardsX = 0.0
        self.MaxSpeedTheta = 0.0
        self.TurningRadius = 0.0
        self.WheelBase = 0.0
        self.GoalToleranceXY = 0.0
        self.GoalToleranceYaw = 0.0
        self.MinimalObstacleDistance = 0.0
        self.ObstacleInflationRadius = 0.0
        self.DynamicObstacleInflationRadius = 0.0
        self.DTRef = 0.0
        self.DTHysteresis = 0.0
        self.IncludeDynamicObstacles = False
        self.IncludeCostmapObstacles = False
        self.AllowOscillationRecovery = False
        self.AllowInitializeWithBackwardMotion = False
        # Deklaracja wiadomoci ustawień
        self.TebParametersReceived = TEB()
        self.TebParametersSaved = TEB()
        #Zmienne pomocnicze
        self.RefreshRate = rospy.Rate(10) #Hz
        self.ConfirmTebSettingsUpdate = False
        while not rospy.is_shutdown():
            try:
                #Deklaracja klienta na zasadzie reconfigure
                self.TebClient = Client('/move_base/TebLocalPlannerROS', timeout=3)
                #Subskrybowanie i publikowanie topicow
                self.parametersSub = rospy.Subscriber('Forklift/cfg/received/teb', TEB,  self.parametersCallback)
                self.parametersPub = rospy.Publisher('Forklift/cfg/current/teb', TEB, queue_size=1, latch=True)
                self.parametersUpdateConfirmationPub = rospy.Publisher('Forklift/cfg/current/teb/confirmation', Bool, queue_size=1, latch=True)
            except (rospy.ServiceException, rospy.ROSException):
                rospy.loginfo('Blad')
            self.Logic()
            self.RefreshRate.sleep()
        while rospy.is_shutdown():
            rospy.loginfo('Rospy is shutted down')
    def parametersCallback(self, msg):
        self.TebParametersReceived = msg
    def UpdateCurrentParameters(self):
        #Zapisanie zaktualizowanych wartosci zmiennych
        self.TebParametersSaved.AccLimitX = self.MaxAccelerationX
        self.TebParametersSaved.AccLimitTheta = self.MaxAccelerationTheta
        self.TebParametersSaved.ForwardMaxVelX = self.MaxSpeedX
        self.TebParametersSaved.BackwardMaxVelX = self.MaxSpeedBackwardsX
        self.TebParametersSaved.MaxVelTheta = self.MaxSpeedTheta
        self.TebParametersSaved.TurningRadius = self.TurningRadius
        self.TebParametersSaved.Wheelbase = self.WheelBase
        self.TebParametersSaved.GoalToleranceXY = self.GoalToleranceXY
        self.TebParametersSaved.GoalToleranceYaw = self.GoalToleranceYaw
        self.TebParametersSaved.MinObstacleDistance = self.MinimalObstacleDistance
        self.TebParametersSaved.ObstacleInflationRadius = self.ObstacleInflationRadius
        self.TebParametersSaved.DynamicObstacleInflationRadius = self.DynamicObstacleInflationRadius
        self.TebParametersSaved.DTRef = self.DTRef
        self.TebParametersSaved.DTHysteresis = self.DTHysteresis
        self.TebParametersSaved.IncludeDynamicObstacles = self.IncludeDynamicObstacles
        self.TebParametersSaved.IncludeCostmapObstacles = self.IncludeCostmapObstacles
        self.TebParametersSaved.OscillationRecovery = self.AllowOscillationRecovery
        self.TebParametersSaved.AllowInitializeWithBackwardMotion = self.AllowInitializeWithBackwardMotion
        self.parametersPub.publish(self.TebParametersSaved)
        self.parametersUpdateConfirmationPub.publish(True)
        
    def UpdateParameters(self):
        rospy.loginfo('Creating parameters table....')
        params = {"max_vel_x": self.MaxSpeedX,
                  "max_vel_x_backwards": self.MaxSpeedBackwardsX,
                  "max_vel_theta": self.MaxSpeedTheta,
                  "acc_lim_x": self.MaxAccelerationX,
                  "acc_lim_theta": self.MaxAccelerationTheta,
                  "min_turning_radius": self.TurningRadius,
                  "wheelbase": self.WheelBase,
                  "xy_goal_tolerance": self.GoalToleranceXY,
                  "yaw_goal_tolerance": self.GoalToleranceYaw,
                  "min_obstacle_dist": self.MinimalObstacleDistance,
                  "inflation_dist": self.ObstacleInflationRadius,
                  "dynamic_obstacle_inflation_dist": self.DynamicObstacleInflationRadius,
                  "dt_ref": self.DTRef,
                  "dt_hysteresis": self.DTHysteresis,
                  "include_dynamic_obstacles": self.IncludeDynamicObstacles,
                  "include_costmap_obstacles": self.IncludeCostmapObstacles,
                  "allow_init_with_backwards_motion": self.AllowInitializeWithBackwardMotion,
                  "oscillation_recovery": self.AllowOscillationRecovery}
        rospy.loginfo('====================CURRENT CONFIG========================')
        config = self.TebClient.update_configuration(params)
        # print(config)
        rospy.loginfo("Update parameters finished...")
    def LoadSavedSettings(self):
        rospy.loginfo("Loading settings from file module started....")
        if not os.path.exists(self.FileDirectory):
            rospy.loginfo('NO SUCH DIRECTORY, CREATING ONE NOW!')
            os.makedirs(self.FileDirectory)
        if os.path.exists(self.FileName):
            with open(self.FileName, 'r') as file:
                settings = json.load(file)
                self.MaxAccelerationX = settings.get("MaxAccelerationX", None)
                self.MaxAccelerationTheta = settings.get("MaxAccelerationTheta", None)
                self.MaxSpeedX = settings.get("MaxSpeedX", None)
                self.MaxSpeedBackwardsX = settings.get("MaxSpeedBackwardsX", None)
                self.MaxSpeedTheta = settings.get("MaxSpeedTheta", None)
                self.TurningRadius = settings.get("TurningRadius", None)
                self.WheelBase = settings.get("WheelBase", None)
                self.GoalToleranceXY = settings.get("GoalToleranceXY", None)
                self.GoalToleranceYaw = settings.get("GoalToleranceYaw", None)
                self.MinimalObstacleDistance = settings.get("MinimalObstacleDistance", None)
                self.ObstacleInflationRadius = settings.get("ObstacleInflationRadius", None)
                self.DynamicObstacleInflationRadius = settings.get("DynamicObstacleInflationRadius", None)
                self.DTRef = settings.get("DTRef", None)
                self.DTHysteresis = settings.get("DTHysteresis", None)
                self.IncludeDynamicObstacles = settings.get("IncludeDynamicObstacles", None)
                self.IncludeCostmapObstacles = settings.get("IncludeCostmapObstacles", None)
                self.AllowOscillationRecovery = settings.get("AllowOscillationRecovery", None)
                self.AllowInitializeWithBackwardMotion = settings.get("AllowInitializeWithBackwardMotion", None)
                # print("ustawienia wczytane z pliku:", settings)
                self.LoadSettingsFromFile = False
                self.UpdateParameters()
        else:
            print("Plik z ustawieniami nie istnieje")
    def SaveSettingsToFile(self):
        print('Zapisuje do pliku!')
        print(os.getcwd())
        settingsToSave = {
                "MaxAccelerationX": self.MaxAccelerationX,
                "MaxAccelerationTheta": self.MaxAccelerationTheta,
                "MaxSpeedX": self.MaxSpeedX,
                "MaxSpeedBackwardsX": self.MaxSpeedBackwardsX,
                "MaxSpeedTheta": self.MaxSpeedTheta,
                "TurningRadius": self.TurningRadius,
                "WheelBase": self.WheelBase,
                "GoalToleranceXY": self.GoalToleranceXY,
                "GoalToleranceYaw": self.GoalToleranceYaw,
                "MinimalObstacleDistance": self.MinimalObstacleDistance,
                "ObstacleInflationRadius": self.ObstacleInflationRadius,
                "DynamicObstacleInflationRadius": self.DynamicObstacleInflationRadius,
                "DTRef": self.DTRef,
                "DTHysteresis": self.DTHysteresis,
                "IncludeDynamicObstacles": self.IncludeDynamicObstacles,
                "IncludeCostmapObstacles": self.IncludeCostmapObstacles,
                "AllowOscillationRecovery": self.AllowOscillationRecovery,
                "AllowInitializeWithBackwardMotion": self.AllowInitializeWithBackwardMotion
            }
        with open(self.FileName, 'w') as file:
            json.dump(settingsToSave, file)
    def Logic(self):
        rospy.loginfo("==================Main Loop==================")
        if self.LoadSettingsFromFile:
            try:
                self.LoadSavedSettings()
            except Exception:
                rospy.loginfo('Blad wczytania danych podczas uruchamiania')
        if self.TebParametersReceived.SaveSettings:
            self.MaxAccelerationX = self.TebParametersReceived.AccLimitX
            self.MaxAccelerationTheta = self.TebParametersReceived.AccLimitTheta
            self.MaxSpeedX = self.TebParametersReceived.ForwardMaxVelX
            self.MaxSpeedBackwardsX = self.TebParametersReceived.BackwardMaxVelX
            self.MaxSpeedTheta = self.TebParametersReceived.MaxVelTheta
            self.TurningRadius = self.TebParametersReceived.TurningRadius
            self.WheelBase = self.TebParametersReceived.Wheelbase
            self.GoalToleranceXY = self.TebParametersReceived.GoalToleranceXY
            self.GoalToleranceYaw = self.TebParametersReceived.GoalToleranceYaw
            self.MinimalObstacleDistance = self.TebParametersReceived.MinObstacleDistance
            self.ObstacleInflationRadius = self.TebParametersReceived.ObstacleInflationRadius
            self.DynamicObstacleInflationRadius = self.TebParametersReceived.DynamicObstacleInflationRadius
            self.DTRef = self.TebParametersReceived.DTRef
            self.DTHysteresis = self.TebParametersReceived.DTHysteresis
            self.IncludeDynamicObstacles = self.TebParametersReceived.IncludeDynamicObstacles
            self.IncludeCostmapObstacles = self.TebParametersReceived.IncludeCostmapObstacles
            self.AllowOscillationRecovery = self.TebParametersReceived.OscillationRecovery
            self.AllowInitializeWithBackwardMotion = self.TebParametersReceived.AllowInitializeWithBackwardMotion
            self.SaveSettingsToFile()
            self.LoadSavedSettings()
            while self.TebParametersReceived.SaveSettings:
                self.UpdateCurrentParameters()
                if not self.TebParametersReceived.SaveSettings:
                    self.parametersUpdateConfirmationPub.publish(False)
                    break
if __name__ == '__main__':
    try:
        rospy.init_node('parameters_configuration')
        parametersService = ParametersService()
        rospy.spin()
        rospy.loginfo('++++++++++++++++++ MAIN ++++++++++++++++++')   
    except rospy.ROSInterruptException as e:
        rospy.logerr("Lifting_module error: %s" % e)
    finally:
        rospy.loginfo('EXIT')