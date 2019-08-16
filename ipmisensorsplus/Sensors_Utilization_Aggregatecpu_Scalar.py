# This sensor is supposed to measure the Utilization of a CPU

class Sensors_Utilization_Aggregatecpu_Scalar(Sensor):
      def __init__(self):
          # Configuration parameters common to all sensors
          self.sensor='Utilization'
          self.device='Aggregatecpu'
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

          # Sensor specific part begins here
          self.openstatfile('/proc/stat')
          self.vars=( 'usr', 'sys', 'idl', 'wai', 'hiq', 'siq' )
          self.init(self.vars)
          
          # Specific to sensors that need to use the two counters
          self.firsttime=True
          self.val['oldtotal']=-10.0
      

      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))

          self.clockvalue=self.timeperiod
          if not self.ready: return None
          self.fd.seek(0)
          self.cn1.update(self.cn2)
          for line in self.fd.readlines():
              l = line.split()
              #if len(l) < 8: continue
              if  l[0] == 'cpu':
                  self.cn2['usr']=long(l[1])+long(l[2])
                  self.cn2['sys']=long(l[3])
                  self.cn2['idl']=long(l[4])
                  if len(l) ==8:
                     self.cn2['wai']= long(l[5])
                     self.cn2['hiq']= long(l[6])
                     self.cn2['siq']= long(l[7])
                  break
          if self.firsttime:
             self.firsttime=False
             return None
          
          for name in self.vars:
              self.val[name]=100.00*(self.cn2[name]-self.cn1[name])/(sum(self.cn2.values())-sum(self.cn1.values()))
          self.val['total']=self.val['usr']+self.val['sys']+self.val['wai']+self.val['hiq']+self.val['siq']
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
sensors['Sensors_Utilization_Aggregatecpu_Scalar']= Sensors_Utilization_Aggregatecpu_Scalar()







