import statvfs

class Sensors_Utilization_Diskpartition_Scalar(Sensor):
      def __init__(self):
          # Configuration parameters common to all sensors
          self.sensor='Utilization'
          self.device='Diskpartition'
          self.valuetype='Scalar'
          self.count='1'
          self.devinst=[]
          self.nodename=os.uname()[1].split('.')[0]
          self.timeperiod=60
          self.clockvalue=self.timeperiod
          self.deadband=5.0
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
          
          # Initial Preparations
          self.ready=False
          self.partitionlist=[]
          # Start with discovering the paritions
          try:
              mtabfile=open('/etc/mtab','r')
              for line in mtabfile:
                  linesplit = line.split()
                  if linesplit[2] in ('binfmt_misc', 'devpts', 'iso9660', 'none', 'proc', 'sysfs', 'usbfs') or linesplit[0] in ('devpts', 'proc', 'none', 'sunrpc', 'usbfs'): continue
                  self.partitionlist.append(linesplit[1])
              mtabfile.close()
              if len(self.partitionlist) > 0:
                 self.ready=True
                 self.vars=tuple(self.partitionlist)
                 self.devinst=[str(i) for i in range(len(self.partitionlist))]
                 fileName='/tmp/Sensor'+self.sensor+self.device+self.valuetype+'.config'
                 file1=open(fileName,'w')
                 file1.write('self.devinst '+str(self.devinst)+'\n')
                 file1.write('self.partitionlist'+str(self.partitionlist)+'\n')
                 file1.close()
                 self.init(self.vars)
          except:
              print "Problem while reading file /etc/mtab in "+str(self.sensor)+str(self.device)
              traceback.print_exc(file=sys.stdout)
              print sys.exc_info()

      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))

          self.clockvalue=self.timeperiod
          if not self.ready: return None

          try:
              for dev in self.devinst:
                  index=int(dev)
                  partitionname=self.partitionlist[index]
                  st=os.statvfs(partitionname)
                  #print partitionname
                  #print self.val[partitionname]
                  utilization=(100.00)-(100.00*float(st[statvfs.F_BAVAIL])/float(st[statvfs.F_BLOCKS]))
                  self.status.processPair('LastReadReadingForDeviceInstance'+self.devinst[index],str(round(utilization,3)))

                  if ((utilization>self.val[partitionname]) and ((utilization-self.val[partitionname])>self.updeadband)) or ((utilization < self.val[partitionname]) and ((self.val[partitionname]-utilization)>self.downdeadband)):
                     self.val[partitionname]=utilization
                     output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst[index]+':'+str(round(self.val[partitionname],3))
                     self.status.processPair('LastReportedReadingForDeviceInstance'+self.devinst[index],str(round(utilization,3)))
                     log(output)

          except:
              print "problem in "+str(self.sensor)+str(self.device)
              traceback.print_exc(file=sys.stdout)
              print sys.exc_info()

          if self.statusCounter==5:
             self.statusCounter=0
             try:
                 self.status.store(open(self.statusFileName,'w'))
             except:
                 traceback.print_exc(file=sys.stdout)
                 print sys.exc_info()
sensors['Sensors_Utilization_Diskpartition_Scalar']= Sensors_Utilization_Diskpartition_Scalar()
