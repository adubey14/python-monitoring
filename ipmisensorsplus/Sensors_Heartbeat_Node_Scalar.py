class Sensors_Heartbeat_Node_Scalar(Sensor):
      def __init__(self):
          # Configuration parameters common to all sensors are here
          self.sensor='Heartbeat'
          self.device='Node'
          self.valuetype='Scalar'
          self.count='1'
          self.nodename=os.uname()[1].split('.')[0]
          self.devinst='0'
          self.timeperiod=300
          self.deadband=0.0
          self.protocolversion='1.0'
          self.updeadband=self.deadband
          self.downdeadband=self.deadband
          self.clockvalue=self.timeperiod
          #Status Properties
          self.status=Properties.Properties()
          self.status.processPair('Name',self.sensor+self.device+self.valuetype)
          self.status.processPair('NodeName',self.nodename)
          self.status.processPair('Timestamp',' ')
          self.statusFileName='/tmp/'+self.nodename+self.sensor+self.device+self.valuetype+'.status'
          self.statusCounter=0

          # Specific to this sensor
          self.firsttime=True
          self.ready=True

      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))

          self.clockvalue=self.timeperiod
          if not self.ready: return None
          if self.firsttime:
             file1=open("/proc/uptime",'r')
             uptime=file1.readline().split()[0]
             output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+'booted'+'%'+uptime
             self.firsttime=False
          else:
             output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+'alive'
          if self.statusCounter==5:
             self.statusCounter=0
             try:
                 self.status.store(open(self.statusFileName,'w'))
             except:
                 traceback.print_exc(file=sys.stdout)
                 print sys.exc_info()
          #print(output)
          logheartbeat(output)




sensors['Sensors_Heartbeat_Node_Scalar']= Sensors_Heartbeat_Node_Scalar()

#







