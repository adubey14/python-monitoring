#This sensor does not report any data
#It is for the sole use of picking up any new sensor present in the directory and invoking it
class Sensors_PluginUse_MonitorforNewSensors(Sensor):
      def __init__(self):
          self.sensor='PluginUse'
          self.device='MonitorforNewSensors'
          self.count='1'
          self.devinst=[]
          self.nodename=os.uname()[1].split('.')[0]



          self.timeperiod=60
          self.clockvalue=self.timeperiod
          #Status Properties
          self.status=Properties.Properties()
          self.status.processPair('Name',self.sensor+self.device)
          self.status.processPair('NodeName',self.nodename)
          self.status.processPair('Timestamp',' ')
          self.status.processPair('ActionsTaken',' ')
          self.status.processPair('LastActionsTaken',' ')

          self.statusFileName='/tmp/'+self.nodename+self.sensor+self.device+'.status'
          self.statusCounter=0
      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))
          #storing the actions taken i.e. the new sensors invoked
          actions=''
          self.clockvalue=self.timeperiod
          #read the entries in the sensor folder
          for root, dirs, files in os.walk(globals()['op'].SensorFolder, topdown=True):
           for name in files:
               if name.startswith('Sensors_') and name.endswith('py'):
                  try:
                      SensorName=name.split('.')[0]
                      if SensorName not in globals()['sensors'].keys():
                         execfile(os.path.join(root,name))
                         print 'Found and added new sensor: '+SensorName
                         actions=actions+'Found and added new sensor: '+SensorName+';'
                      elif name in globals()['sensorsModTime'].keys():
                           modtime=os.path.getmtime(os.path.join(root,name))
                           if modtime > globals()['sensorsModTime'][name]:
                             execfile(os.path.join(root,name))
                             globals()['sensorsModTime'][name]=modtime
                             print 'Invoked new version of : '+SensorName
                             actions=actions+'Invoked new version of : '+SensorName+';'
                  except Exception, e:
                      traceback.print_exc(file=sys.stdout)
                      print sys.exc_info()
          actions=actions.strip()
          self.status.setProperty('ActionsTaken',actions)
          if len(actions)!=0:
             self.status.setProperty('LastActionsTaken',actions)

          if self.statusCounter==5:
             self.statusCounter=0
             try:
                 self.status.store(open(self.statusFileName,'w'))
             except:
                 traceback.print_exc(file=sys.stdout)
                 print sys.exc_info()



sensors['Sensors_PluginUse_MonitorforNewSensors']= Sensors_PluginUse_MonitorforNewSensors()

