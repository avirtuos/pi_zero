#!/usr/bin/python

'''
  Here is some sample data from the MPU-9255 IMU.
  {'pressureValid': False, 
    'accelValid': True, 
    'temperature': 0.0, 
    'pressure': 0.0, 
    'fusionQPoseValid': True, 
    'timestamp': 1471314050076560L, 
    'compassValid': True, 
    'compass': (26.2247257232666, 36.678741455078125, -17.60536003112793), 
    'accel': (0.0107421875, 1.013427734375, -0.03369140625), 
    'humidity': 0.0, 'gyroValid': True, 
    'gyro': (0.00553120207041502, -0.0031295656226575375, 0.0031766612082719803), 
    'temperatureValid': False, 
    'humidityValid': False, 
    'fusionQPose': (0.6710100769996643, 0.6879799365997314, -0.20192061364650726, -0.18883132934570312), 
    'fusionPoseValid': True, 
    'fusionPose': (1.5989785194396973, -0.011157416738569736, -0.5601144433021545)}
'''

import sys, getopt
sys.path.append('.')
import RTIMU
import os.path
import time
   
SETTINGS_FILE = "RTIMULib.ini"  
   
s = RTIMU.Settings(SETTINGS_FILE)
imu = RTIMU.RTIMU(s)  
   
if (not imu.IMUInit()):  
  sys.exit(1)  
   
imu.setSlerpPower(0.02)  
imu.setGyroEnable(True)  
imu.setAccelEnable(True)  
imu.setCompassEnable(True)  
   
poll_interval = imu.IMUGetPollInterval()  
   
while True:  
  hack = time.time()  

  if imu.IMURead():  
    data = imu.getIMUData()  
    print data
  
  time.sleep(poll_interval*1.0/1000.0)