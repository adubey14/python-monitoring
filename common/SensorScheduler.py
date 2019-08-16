# coding: utf-8
###############################################################################
'''
This version of SensorScheduler will only work with python2.5
List of Exit Codes
1   incompatible python version.
2   could not load libc.so.6
3   improper command arguments
'''
###############################################################################

def debugprintf(output):
    #print "debug___:"+output
    return
#_______________ Global Variables _________________________#
global PreviousTS
PreviousTS=-1
global Iterm
Iterm=0.0
global sensors,incr,totaldrift,sensorsModTime
sensors ={}
sensorsModTime={}
incr =0
global jitterwindow,starttimestamp,positivejitter,changeinjitter,lastjitter
starttimestamp=0.0
jitterwindow ={}
positivejitter=0.0
changeinjitter=0.0
lastjitter=0.0

#______________    Start: Check Python Version ______________________#
import sys,traceback
def checkPyVer():
    if sys.version_info < (2, 5):
       print "You are using python ",sys.version
       print "In order to use fine grained control over jitter we require python2.5"
       sys.exit(1)

checkPyVer()
#______________    End: Check Python Version ______________________#

#______________    Start: Define NanoSleep function ______________________#
NANO=1000000000 # A constant equivalent to 1 second
from ctypes import *
try:
    libc=CDLL("libc.so.6")
except:
    traceback.print_exc(file=sys.stdout)
    print sys.exc_info()
    sys.exit(2)

class timespec(Structure):
      _fields_ = [('secs', c_long),('nsecs', c_long),]

libc.nanosleep.argtypes = [POINTER(timespec), POINTER(timespec)]

global avgerr
avgerr=0.0

def nanosleep(nanoseconds):
    nanoseconds=max(0,nanoseconds-long(globals()['avgerr']*NANO))
    #print avgerr
    #print nanoseconds
    sec=nanoseconds//NANO
    nsec=nanoseconds%NANO
    timetosleep=timespec(sec,nsec)
    remainingtime=timespec(0,0)
    libc.nanosleep(timetosleep,remainingtime)
    return(remainingtime.secs*NANO+remainingtime.nsecs)
#______________    END: Define NanoSleep function ______________________#

#______________    Start: Benchmarking NanoSleep function ______________________#
def benchmarkSleep():
    error=0.0
    ITERATIONS=10
    for i in range (ITERATIONS):
        ct=time.time()
        nanosleep(NANO)
        ot=time.time()
        error=error+ot-ct-1.0
    globals()['avgerr']=float(error)/float(ITERATIONS)
    #print "average error in sleep is "+str(avgerr)

#______________    Other Require Modules ______________________#
import os, re, time, types, signal, gc,string,commands,shutil,Properties,automaticIPMIconfig
import datetime
from string import Template
from math import ceil
#_____________________ Start: Synchronization Function___________________________#
'''
This function will use the nanosleep to sleep till next 5th minute of the hour. By waiting till that time it will allow other sensors enough time to start.
'''
global startDateTime
global currentSyncTime

def syncToNextPlusOneFifthMinute():
    currentDateTime=datetime.datetime.now()
    currentTime=currentDateTime.time()
    seconds_since_start_of_day=currentTime.hour*3600.0+currentTime.minute*60.0+currentTime.second*1.0+currentTime.microsecond/1e6
    seconds_to_next_fifth_minute=600-(seconds_since_start_of_day%300)
    #Now sleep till next fifth second
    #nanosleep(int(seconds_to_next_fifth_minute*NANO))
    globals()['startDateTime']=currentDateTime
    #+datetime.timedelta(seconds=int(ceil(seconds_to_next_fifth_minute)),microseconds=int(1e6*(seconds_to_next_fifth_minute-ceil(seconds_to_next_fifth_minute))))
    globals()['currentSyncTime']=globals()['startDateTime']

#___________________End : Synchronization Function ___________________________#

#______________    Start: Sensor Class ______________________#
'''Sensor is the super class of all sensors
It will help in setting a dictionary of counters; two counters cn1, cn2 to get the update in the values over the last time period
these values differ for every sensor
'''
class Sensor:
      def __init__(self):
          #self.timeperiod=10 #default timeperiod is 10 seconds
          self.clockvalue=self.timeperiod
          self.ready=False  #By default,sensor is not ready

      def __cmp__(self,other):
          return cmp(self.clockvalue,other.clockvalue)
      def init(self, vars=()):
          if vars:
             self.val = {}; self.cn1 = {}; self.cn2 = {}
             for name in vars:
                 self.val[name] = self.cn1[name] = self.cn2[name] = 0

      def initializeClock(self):
          self.clockvalue=self.timeperiod
          debugprintf('Initialized Clock')

      def openstatfile(self, file):
          "Open stat file descriptor"
          self.statfile = file
          self.fd = statopen(file)
          if self.fd :
             self.ready=True
      def gettimeperiod(self):
          return self.timeperiod
      def updateclockbydecr(self,time):
          self.clockvalue=self.clockvalue-time
#______________    End: Sensor Class ______________________#


#______________   Start: Options ______________________#

class Options:
      def __init__(self, args=''):
          self.args = args
          self.count = -1
          self.debug = 0
          self.output = False
          self.printout=False
          self.syslogit=False
	  self.profile=False
	  self.debug=False
	  self.force=False
	  self.control=True
	  self.profilemax=0.0
	  self.noofiterations=-1
	  self.SensorFolder=''
          self.parseargs()
      def parseargs(self):
          try:
              import getopt
              options, arguments = getopt.getopt (self.args[1:], 'Spschd',['Sensors=','print', 'syslog', 'checkprofile','help','debug','pdb',])
          except getopt.error, exc:
              self.printusage()
              sys.exit(-1)
          for option,argument in options:
              if option in ['-S','--Sensors']:
                 self.SensorFolder=argument
              if option in ['-p','--print']:
                 self.printout=True
              if option in ['-s','--syslog']:
                 self.syslogit=True
              if option in ['-c','--checkprofile']:
                 self.profile=True
              if option in ['-d','--debug']:
                 self.debug=True
                 self.profile=True
                 self.printout=True
              if option in ['-h','--help']:
                 self.printusage()
                 sys.exit(0)
              if option in ['--pdb',]:
                 self.debug=True
                 self.profile=True
                 self.printout=True
                 import pdb
                 pdb.set_trace()
          if self.profile:
             self.profileFile=open('/tmp/SensorProfile.log','w')
          if (not self.printout) and (not self.syslogit) and (not self.profile):
             print "Wrong Usage"
             self.printusage()
             sys.exit(3)

          checkPyVer()

      def printusage(self):
          print 'usage: ',self.args[0], ' [options..]'
          print '''Atleast one option is required. The options are:
-p,--print        : Print the output to screen
-s,--syslog       : Send the health data to syslog
-c,--checkprofile : Profile the Sensors for jitter
-d,--debug        : Print extra info that will help in debugging
--pdb             : Invoke the python debugger
-h,--help         : Print usage help
-S,--Sensors=[]   : Path to sensors folder
'''
#______________   End: Options ______________________#

def log(output):
	try:
		if op.printout:
			print output
	
#sends to MongoDB here

# ’output’ message format (delimited by ‘:’)
# protocol version
# timestamp
# nodename
# sensor
# device
# valuetype
# count
# devinst
# val	

			posts = db.posts
			toParse=output.split(":")
			
			post = {“protocol_version”: str(toParse[0]),
				“timestamp”: toParse[1],
				“nodename”: toParse[2],
				“sensor”: toParse[3],
				“device”: toParse[4],
				“valuetype”: toParse[5],
				“count”: toParse[6],
				“devinst”: toParse[7],
				“val”: toParse[8]}
			posts.insert_one(post) 

		#if op.syslogit:
       #   syslog.syslog(syslog.LOG_NOTICE,output)
	except Exception, e:
		traceback.print_exc(file=sys.stdout)
		print sys.exc_info()

global HearHeartBeatSequenceNumber
HeartBeatSequenceNumber=0
def logheartbeat(output):
    globals()['HeartBeatSequenceNumber']=globals()['HeartBeatSequenceNumber']+1
    output=str(globals()['HeartBeatSequenceNumber'])+":"+output
    try:
       if op.printout:
          print output
       #if op.syslogit:
         # syslog.closelog()
         # syslog.openlog('HEARTBEAT',syslog.LOG_NOWAIT,syslog.LOG_USER)
         # syslog.syslog(syslog.LOG_NOTICE,output)
         # syslog.closelog()
         # syslog.openlog('HEALTH',syslog.LOG_NOWAIT,syslog.LOG_USER)
    except Exception, e:
       traceback.print_exc(file=sys.stdout)
       print sys.exc_info()

def statopen(file):
	"Open a file for reuse, if already opened, return file descriptor"
	global fds
	if not os.path.exists(file): return None
	if 'fds' not in globals().keys(): fds = {}
	if file not in fds.keys():
		fds[file] = open(file, 'r', 0)
	else:
		fds[file].seek(0)
	return fds[file]

def boottime():
    "Return the number of seconds since bootup"
    try:
        for line in open('/proc/uptime', 'r', 0).readlines():
            l = line.split()
            if len(l) < 2: continue
            return float(l[0])
    except:
        for line in statopen('/proc/stat').readlines():
            l = line.split()
            if len(l) < 2: continue
            if l[0] == 'btime':
               return time.time() - long(l[1])



#______________   Start: Signal handlers ______________________#
def syncSignalHandler(signum,frame):
    for name in sensors.keys():
        debugprintf(name)
        sensors[name].initializeClock()
    globals()['incr']=0
    globals()['totaldrift']=0
    globals()['Iterm']=0
    globals()['PreviousTS']=-1
    debugprintf("Handled Sync Signal")


def stopProcess(signum,frame):
    outMessage=protocolversion+':'+str((time.time())).split('.')[0]+':'+nodename+':'+sensor+':'+device+':'+valuetype+':'+count+':'+devinst+':'+'0'
    log(outMessage)
    sys.exit(0)

#______________   END: Signal handlers ______________________#

#______________   Start: Main Sensor Scheduler Function ______________________#
def startSensing():
    #This has to be repeated continuously
    while True:
          CurrentTS=str((time.time()))
          sensor_keys=sensors.keys()
          sensor_keys.sort()
          for name in sensor_keys:
              sensors[name].updateclockbydecr(globals()['incr'])
              if sensors[name].clockvalue==0:
                 try:
		    #adding two lines for profiling each sensor
	            if globals()['op'].profile:
                          globals()['op'].profileFile.write(name+":entry:"+str((time.time()))+'\n')
                    timestamp=CurrentTS.split('.')[0]
                    sensors[name].senseandlog(timestamp)
	            if globals()['op'].profile:
                          globals()['op'].profileFile.write(name+":exit:"+str((time.time()))+'\n')
                 except Exception, e:
                    traceback.print_exc(file=sys.stdout)
                    print sys.exc_info()
              if sensors[name].clockvalue<0:
                 try:
                     #adding two lines for profiling each sensor
                     if globals()['op'].profile:
                        globals()['op'].profileFile.write(name+":entry:"+str((time.time()))+'\n')
                     sensors[name].senseandlog(timestamp)
                     if globals()['op'].profile:
                        globals()['op'].profileFile.write(name+":exit:"+str((time.time()))+'\n')
                 except Exception, e:
                        traceback.print_exc(file=sys.stdout)
                        print sys.exc_info()
                 del sensors[name]
          sensor_obj_list=sensors.values()
          if len(sensor_obj_list)==0: return None
          sensor_obj_list.sort()
          globals()['incr']=sensor_obj_list[0].clockvalue
          if globals()['op'].profile:
             globals()['op'].profileFile.write(str(globals()['currentSyncTime'])+'\n')
             globals()['op'].profileFile.write("#####################################"+'\n')
          globals()['currentSyncTime']= globals()['currentSyncTime']+datetime.timedelta(seconds=globals()['incr'])
          myTime=datetime.datetime.now()
          nowTime= datetime.datetime.now()
          if nowTime<globals()['currentSyncTime']:
             timediff=globals()['currentSyncTime']- nowTime
             timediff_sec=timediff.seconds*1.0+timediff.microseconds/1e6
          else:
               timediff_sec=0
          timediff_nanosec=round(1e9*(timediff_sec))
          sleeptime=max(0,int(timediff_nanosec))
          remainingns=nanosleep(sleeptime)
          debugprintf("Out of sleep in Sensing")

#______________   End: Main Sensor Scheduler Function ______________________#
sensor='Status'
device='Monitoringframework'
valuetype='Scalar'
count='1'
devinst='0'
nodename=os.uname()[1].split('.')[0]
protocolversion='1.0'

import pymongo

#______________   Begin:Main Function ______________________#
if __name__=='__main__':
   try:
	client = MongoClient(‘localhost’,’27017’)
	db = client.sensor_info
	
	
       op=Options(sys.argv)
       #checkUniqueInstance()
       gc.collect()
       #syslog.openlog('HEALTH',syslog.LOG_NOWAIT,syslog.LOG_USER)
       signal.signal(signal.SIGTERM,stopProcess)
       #benchmarkSleep();
       outMessage=protocolversion+':'+str((time.time())).split('.')[0]+':'+nodename+':'+sensor+':'+device+':'+valuetype+':'+count+':'+devinst+':'+'1'
       log(outMessage)
       '''
       The sensor scheduler will send following messages
       1: sensor scheduler is up
       0: sensor scheduler went down properly
       -1: sensor scheduler went down due to some error.
       '''
       incr=10 # this is a default wait. If there is no sensor it will atleast wait for this time
       if len(globals()['op'].SensorFolder)==0:
          globals()['op'].SensorFolder='./sensors'
       for root, dirs, files in os.walk(globals()['op'].SensorFolder, topdown=True):
           for name in files:
               if name.startswith('Sensors_') and name.endswith('py'):
                  print os.path.join(root,name)
                  try:
                      modtime=os.path.getmtime(os.path.join(root,name))
                      execfile(os.path.join(root,name))
                      globals()['sensorsModTime'][name]=modtime
                  except Exception, e:
                      traceback.print_exc(file=sys.stdout)
                      print sys.exc_info()
                  print sensors.keys()
       sensor_obj_list=sensors.values()
       if len(sensor_obj_list)!=0:
          sensor_obj_list.sort()
          incr=sensor_obj_list[0].clockvalue
       else:
            print "No sensor in the specified directory: "+globals()['op'].SensorFolder
            sys.exit(-1)

       debugprintf ("Starting synchronization to the next plus one fith minute in the hour")
       syncToNextPlusOneFifthMinute()
       globals()['currentSyncTime']= globals()['currentSyncTime']+datetime.timedelta(seconds=globals()['incr'])
       nowTime= datetime.datetime.now()
       if nowTime<globals()['currentSyncTime']:
          timediff=globals()['currentSyncTime']- nowTime
          timediff_sec=timediff.seconds*1.0+timediff.microseconds/1e6
       else:
          timediff_sec=0

       timediff_nanosec=round(1e9*(timediff_sec))
       sleeptime=max(0,int(timediff_nanosec))
       #remainingns=nanosleep(sleeptime)
       debugprintf("Start Sensing")
       startSensing()

   except KeyboardInterrupt, e:
       outMessage=protocolversion+':'+str((time.time())).split('.')[0]+':'+nodename+':'+sensor+':'+device+':'+valuetype+':'+count+':'+devinst+':'+'0'
       log(outMessage)
       os.system('rm -f /tmp/.SensorScheduler/lock_sense.pid')
   except Exception, f:
       outMessage=protocolversion+':'+str((time.time())).split('.')[0]+':'+nodename+':'+sensor+':'+device+':'+valuetype+':'+count+':'+devinst+':'+'-1'
       log(outMessage)
       traceback.print_exc(file=sys.stdout)
       print sys.exc_info()


