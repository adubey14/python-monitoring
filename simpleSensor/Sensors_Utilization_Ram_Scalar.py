#Free Memory Utilization sensor.
# It is assumed that values in proc stat are in KB

class Sensors_Utilization_Ram_Scalar(Sensor):
      def __init__(self):
          # Configuration parameters common to all sensors
          self.sensor='Utilization'
          self.device='Ram'
          self.valuetype='Scalar'
          self.count='1'
          self.devinst='0'
          self.nodename=os.uname()[1].split('.')[0]
          self.timeperiod=10
          self.clockvalue=self.timeperiod
          self.deadband=7.0
          self.protocolversion='1.0'
          self.updeadband=self.deadband
          self.downdeadband=self.deadband
          #Status Properties
          self.status=Properties.Properties()
          self.status.processPair('Name',self.sensor+self.device+self.valuetype)
          self.status.processPair('NodeName',self.nodename)
          self.status.processPair('Timestamp',' ')
          self.status.processPair('LastReadReading','-1')
          self.status.processPair('LastReportedReading','-1')
          self.statusFileName='/tmp/'+self.nodename+self.sensor+self.device+self.valuetype+'.status'
          self.statusCounter=0

          # Specific to this sensor
          self.openstatfile('/proc/meminfo')
          self.vars=( 'MemUsed', 'Buffers', 'Cached', 'MemFree','MemTotal', 'SwapCached')
          self.init(self.vars)
          self.val['oldtotal']=-10.0



      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))

          self.clockvalue=self.timeperiod
          if not self.ready: return None
          self.fd.seek(0)
          for line in self.fd.readlines():
              l = line.split()
              if len(l) < 2: continue
              name = l[0].split(':')[0]
              if name in self.vars:
                 self.val[name] = long(l[1]) * 1024.0

          self.val['MemUsed'] = self.val['MemTotal'] - self.val['MemFree'] - self.val['Buffers'] - self.val['Cached']
          self.val['total']=(100.00*(self.val['MemUsed']/self.val['MemTotal']))
          self.status.setProperty('LastReadReading',str(self.val['total']))
          if (self.val['total']> self.val['oldtotal']) and (self.val['total']-self.val['oldtotal']>self.updeadband):
             self.val['oldtotal']=self.val['total']
             output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+str(round(self.val['total'],3))
             self.status.setProperty('LastReportedReading',str(self.val['total']))
             log(output)
          elif (self.val['total']< self.val['oldtotal']) and (self.val['oldtotal']-self.val['total']>self.downdeadband):
             self.val['oldtotal']=self.val['total']
             output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+str(round(self.val['total'],3))
             self.status.setProperty('LastReportedReading',str(self.val['total']))
             log(output)
          if self.statusCounter==5:
             self.statusCounter=0
             try:
                 self.status.store(open(self.statusFileName,'w'))
             except:
                 traceback.print_exc(file=sys.stdout)
                 print sys.exc_info()

sensors['Sensors_Utilization_Ram_Scalar']= Sensors_Utilization_Ram_Scalar()

#







