#!/bin/sh
# Shell script to start the worker node sensor reader script.
# This script had to be written to bypass the inittab command line
# length restriction. Until we find a better way to do this, this
# should do.
# 
# abhishek dubey 

#define the monitoring sensor path
export MONITORING_SENSOR_PATH=''

/usr/bin/pkill -u root -f "/usr/local/Python-2.5.1/bin/python SensorScheduler.py -s --Sensors=../sensors"
/usr/bin/pkill -u root runSensorScheduler.sh
cd common

/usr/local/Python-2.5.1/bin/python -u SensorScheduler.py -s --Sensors=../sensors/ >> /tmp/scriptout.log
