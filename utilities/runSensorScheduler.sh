#!/bin/sh
# Shell script to start the worker node sensor reader script.
# This script had to be written to bypass the inittab command line
# length restriction. Until we find a better way to do this, this
# should do.
# 
# amitoj@fnal.gov     Date: 7/30/2007
#

/usr/bin/pkill -u root -f "/usr/local/Python-2.5.1/bin/python SensorScheduler.py -s --Sensors=../sensors"
/usr/bin/pkill -u root runSensorScheduler.sh
cd /usr/local/monitoring_db/data_sources/common
/usr/local/Python-2.5.1/bin/python -u SensorScheduler.py -s --Sensors=../sensors/ >> /tmp/scriptout.log
