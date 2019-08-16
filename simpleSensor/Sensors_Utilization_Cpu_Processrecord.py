#Process Utilization Sensor

class Sensors_Utilization_Cpu_Processrecord(Sensor):
      def __init__(self):
          # Configuration parameters common to all sensors
          self.sensor='Utilization'
          self.device='Cpu'
          self.valuetype='Processrecord'
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
          self.statusFileName='/tmp/'+self.nodename+self.sensor+self.device+self.valuetype+'.status'
          self.statusCounter=0

          #Specific for this sensor
          self.vars=('oldjiffies','newjiffies')
          self.oldcpureading=0
          self.newcpureading=0
          # Specific for sensors that need to use the two counters
          self.firsttime=True
          self.val={}
          self.processargs={}
          self.cn1={}
          self.cn2={}
          self.openstatfile('/proc/stat')


      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))
          self.clockvalue=self.timeperiod
          if not self.ready: return None
          self.fd.seek(0)
          self.oldcpureading=self.newcpureading
          #print 'oldcpu %d' %self.oldcpureading
          self.cn1.clear()
          self.cn1.update(self.cn2)
          self.cn2.clear()
          currentPIDList=[]
          for pid in os.listdir('/proc/'):
              try:
                   currentPIDList.append(int(pid))
              except: 
                      continue
          currentpidlist=currentPIDList
          for key in self.val.keys():
              if key not in currentpidlist:
                 del self.val[key]
                 del self.processargs[key]
                 #print 'Termination of process %s detected at timestamp %s'%(key,timestamp)


          for line in self.fd.readlines():
              l = line.split()
              if  l[0] == 'cpu':
                if len(l)<8:
                   self.newcpureading=long(l[1])+long(l[2])+long(l[3])+long(l[4])
                else:
                   self.newcpureading=long(l[1])+long(l[2])+long(l[3])+long(l[4])+long(l[5])+long(l[6])+long(l[7])
              break

          #print 'newcpu %d'%self.newcpureading
          if self.firsttime:
             self.firsttime=False
             return None

          #print 'cpu diff: %d'%(self.newcpureading - self.oldcpureading)
          for pid in currentPIDList:
             if os.path.exists('/proc/%s/stat' % pid):
#                if not self.cn1.has_key(pid): self.cn1[pid]=0
                 try:
                     l=open('/proc/%s/stat' % pid).read().split()
                     uid=os.stat('/proc/%s/stat' % pid)[4]
                     self.cn2[pid]=long(l[13])+long(l[14])
                     #read the memory information
                     if not self.val.has_key(pid):
                        tempd=open('/proc/%s/cmdline' % pid)
                        tempvar=tempd.read()
                        tempd.close()
                        tempvar=re.sub(r'\s','%',tempvar)
                        tempvar=re.sub(r'\x00','%',tempvar)
                        tempvar=re.sub(r':','%',tempvar)
                        self.processargs[pid]=tempvar
                     if self.cn1.has_key(pid):
                        #self.val[pid]=float(self.cn2[pid]-self.cn1[pid])/(self.newcpureading - self.oldcpureading)
                        tempval=100.0*float(self.cn2[pid]-self.cn1[pid])/(self.newcpureading - self.oldcpureading)
                        #print 'pid:%s percent:%f'%(pid,tempval)
                        if not self.val.has_key(pid):
                           if len(self.processargs[pid])!=0:
                              self.val[pid]=tempval
                              output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(tempval,3))
                              log(output)
                        else:
                           if len(self.processargs[pid])!=0:
                              if (((tempval> self.val[pid]) and (tempval- self.val[pid])>self.updeadband) or ((tempval< self.val[pid]) and (self.val[pid] -tempval )>self.downdeadband)):
                                 self.val[pid]=tempval
                                 output=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor+':'+self.device+':'+self.valuetype+':'+ self.count+':'+self.devinst+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(tempval,3))
                                 log(output)

                 except:
                     traceback.print_exc(file=sys.stdout)
                     print sys.exc_info()
                     if self.cn2.has_key(pid): del self.cn2[pid]

          if self.statusCounter==5:
             self.statusCounter=0
             try:
                 self.status.store(open(self.statusFileName,'w'))
             except:
                 traceback.print_exc(file=sys.stdout)
                 print sys.exc_info()

sensors['Sensors_Utilization_Cpu_Processrecord']= Sensors_Utilization_Cpu_Processrecord()

#







