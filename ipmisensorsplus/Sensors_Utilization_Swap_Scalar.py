class Sensors_Utilization_Swap_Scalar(Sensor):

	def __init__(self):
                # Configuration parameters common to all sensors
                self.sensor='Utilization'
                self.device='Swap'
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

                #Specific to this sensor
                self.openstatfile('/proc/swaps')
		self.vars = ('used', 'total')
		self.init(self.vars)
                self.val['oldreading']=-10.0
                self.val['reading']=0.0

        def senseandlog(self,timestamp):
                #Setting Status Property
                self.statusCounter=self.statusCounter+1
                self.status.setProperty('Timestamp',str(timestamp))

                self.clockvalue=self.timeperiod
                if not self.ready: return None
                self.val['used']=0
                self.val['total']=0
                self.fd.seek(0)
                for line in self.fd.readlines():
                    l = line.split()
                    if len(l) < 5 or l[0] == 'Filename': continue
                    self.val['total']= long(l[2])*1024.0
                    self.val['used']= self.val['used'] + long(l[3])*1024.0
                    self.val['reading']=100.0*self.val['used']/self.val['total']
                self.status.setProperty('LastReadReading',str(self.val['reading']))
                if (self.val['reading']> self.val['oldreading']) and (self.val['reading']-self.val['oldreading']>self.updeadband):
                   self.val['oldreading']=self.val['reading']
                   output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+str(round(self.val['reading'],3))
                   self.status.setProperty('LastReportedReading',str(self.val['reading']))
                   log(output)
                elif (self.val['reading']< self.val['oldreading']) and (self.val['oldreading']-self.val['reading']>self.downdeadband):
                   self.val['oldreading']=self.val['reading']
                   self.status.setProperty('LastReportedReading',str(self.val['reading']))
                   output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+str(round(self.val['reading'],3))
                   log(output)
                if self.statusCounter==5:
                   self.statusCounter=0
                   try:
                       self.status.store(open(self.statusFileName,'w'))
                   except:
                       traceback.print_exc(file=sys.stdout)
                       print sys.exc_info()


sensors['Sensors_Utilization_Swap_Scalar']= Sensors_Utilization_Swap_Scalar()

