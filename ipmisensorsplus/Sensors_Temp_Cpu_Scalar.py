class Sensors_Temp_Cpu_Scalar(Sensor):
      def __init__(self):
          # Configuration parameters common to all sensors
          self.sensor='Temp'
          self.device='Cpu'
          self.valuetype='Scalar'
          self.count='1'
          self.devinst=['0']
          self.nodename=os.uname()[1].split('.')[0]
          self.timeperiod=10
          self.clockvalue=self.timeperiod
          self.deadband=2.0
          self.protocolversion='1.0'
          self.updeadband=self.deadband
          self.downdeadband=self.deadband

          #Status Properties
          self.status=Properties.Properties()
          self.status.processPair('Name',self.sensor+self.device+self.valuetype)
          self.status.processPair('NodeName',self.nodename)
          self.status.processPair('Timestamp',' ')
          self.statusFileName='/tmp/'+self.nodename+self.sensor+self.device+self.valuetype+'.status'
          self.statusCounter=0



          # Specific to this sensor
          self.sdrname='/tmp/localsdr.sdr'
          self.firsttime=True

          #check if ready or not
          tmp=open('/proc/devices').read()
          if string.find(tmp,'ipmidev')!=-1:
               if not os.path.exists(self.sdrname):
                  commands.getstatusoutput('ipmitool sdr dump %s'%self.sdrname)
               self.ready=True
          else:
               print 'cannot use ipmi local on host %s' %self.nodename
               self.ready=False

          # Writing the automatic IPMI Config section
          EntityName='Processor'
          IdentifierName='degrees'
          
          # hard coding the ipmi dev query strings for pion cluster
          if 'pion' not in self.nodename:
             self.IPMIDevQueryString=automaticIPMIconfig.config(self.sdrname,EntityName,IdentifierName)
          else:
             self.IPMIDevQueryString=['Proc1 Core temp']


          if len(self.IPMIDevQueryString)!=0:
             self.vars=tuple(self.IPMIDevQueryString)
             self.devinst=[str(i) for i in range(len(self.IPMIDevQueryString))]
             fileName='/tmp/Sensor'+self.sensor+self.device+self.valuetype+'.config'
             file1=open(fileName,'w')
             file1.write('self.devinst '+str(self.devinst)+'\n')
             file1.write('self.IPMIDevQueryString '+str(self.IPMIDevQueryString)+'\n')
             file1.close()
          else:
             self.ready=False
          
          if len(self.IPMIDevQueryString)!=0:
             self.init(self.vars)



      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))



          self.clockvalue=self.timeperiod
          if not self.ready: return None
          IPMICommandTemplate=Template('ipmitool -S ${sdrname} sensor reading \"${querystring}\"')
          counter=-1;
          for ipmiquery in self.IPMIDevQueryString:
              counter=counter+1;
              try:
                  reading=float(commands.getoutput(IPMICommandTemplate.substitute(sdrname=self.sdrname,querystring=ipmiquery)).split('|')[1].split()[0])
                  self.status.processPair('LastReadReadingForDeviceInstance'+self.devinst[counter],str(round(reading,3)))
              except:
                     print "error in running ipmi command in Sensors_Temp_Cpu_Scalar"
                     self.status.processPair('LastReadReadingForDeviceInstance'+self.devinst[counter],'error in running ipmi command'+str(sys.exc_info()))
                     print "The command given was %s"%IPMICommandTemplate.substitute(sdrname=self.sdrname,querystring=ipmiquery)
                     traceback.print_exc(file=sys.stdout)
                     print sys.exc_info()
                     continue
              if (self.val[ipmiquery]> reading) and (self.val[ipmiquery]- reading >self.downdeadband):
                   self.val[ipmiquery]=reading
                   output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst[counter]+':'+str(round(reading,3))
                   self.status.processPair('LastReportedReadingForDeviceInstance'+self.devinst[counter],str(round(reading,3)))
                   log(output)
                   continue
              elif (self.val[ipmiquery]< reading) and (reading -self.val[ipmiquery] >self.updeadband):
                   self.val[ipmiquery]=reading
                   output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst[counter]+':'+str(round(reading,3))
                   self.status.processPair('LastReportedReadingForDeviceInstance'+self.devinst[counter],str(round(reading,3)))
                   log(output)
                   continue
              else:
                   continue

          if self.statusCounter==5:
             self.statusCounter=0
             try:
                 self.status.store(open(self.statusFileName,'w'))
             except:
                 traceback.print_exc(file=sys.stdout)
                 print sys.exc_info()

sensors['Sensors_Temp_Cpu_Scalar']= Sensors_Temp_Cpu_Scalar()

#







