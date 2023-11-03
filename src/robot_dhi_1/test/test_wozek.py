#!/usr/bin/env python3

import importlib.util
import unittest


spec = importlib.util.spec_from_file_location("wozek", "/home/ros/catkin_ws/src/robot_dhi_1/scripts/wozek.py")
wozek = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wozek)
wozek = wozek.WozekModbusDriver

class TestWozek(unittest.TestCase):
    def test_move_servo(self):
        pass

    def test_move_motor(self):
        pass

    def test_servo_callback(self):
        pass

    def test_wozek_callback(self):
        pass

    def test_servo_angle_callback(self):
        pass

    def test_wozek_angle_callback(self):
        pass

if __name__ == '__main__':
    unittest.main()