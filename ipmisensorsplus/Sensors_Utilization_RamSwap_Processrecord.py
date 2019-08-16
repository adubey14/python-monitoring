#Process Utilization Sensor

class Sensors_Utilization_RamSwap_Processrecord(Sensor):
      def __init__(self):
          # Configuration parameters common to all sensors
          self.sensor=['Utilization','Utilization']
          self.device=['Ram','Swap']
          self.valuetype='Processrecord'
          self.count=['1','1']
          self.devinst=['0','0']
          self.nodename=os.uname()[1].split('.')[0]
          self.timeperiod=10
          self.clockvalue=self.timeperiod
          self.deadband=[7.0,7.0]
          self.protocolversion='1.0'
          self.updeadband=self.deadband
          self.downdeadband=self.deadband
          #Status Properties
          self.status=Properties.Properties()
          self.status.processPair('Name','UtilizationRamSwap'+self.valuetype)
          self.status.processPair('NodeName',self.nodename)
          self.status.processPair('Timestamp',' ')
          self.statusFileName='/tmp/'+self.nodename+'UtilizationRamSwap'+self.valuetype+'.status'
          self.statusCounter=0
          #Specific for this sensor
          self.firsttime=True
          self.val={}
          self.processargs={}
          self.swappercent={}
          self.rampercent={}
          self.ramtotal=0
          self.swaptotal=0
          self.ready=True
          for line in open('/proc/meminfo').readlines():
              l=line.split()
              if len(l) < 2: continue
              name = l[0].split(':')[0]
              if name=='MemTotal': self.ramtotal= long(l[1]) * 1024
              if name=='SwapTotal': self.swaptotal=long(l[1]) * 1024
              if self.ramtotal!=0 and self.swaptotal!=0: break #i.e. we have read the values



      def senseandlog(self,timestamp):
          #Setting Status Property
          self.statusCounter=self.statusCounter+1
          self.status.setProperty('Timestamp',str(timestamp))
          self.clockvalue=self.timeperiod
          if not self.ready: return None
          currentPIDList=[]
          for pid in os.listdir('/proc/'):
              try: 
                   currentPIDList.append(int(pid))
              except: 
                      continue

          for key in self.val.keys():
              if key not in currentPIDList:
                 del self.val[key]
                 del self.processargs[key]
                 del self.rampercent[key]
                 del self.swappercent[key]
                 #print 'Termination of process %s detected at timestamp %s'%(key,timestamp)

          #print 'cpu diff: %d'%(self.newcpureading - self.oldcpureading)
          for pid in currentPIDList:
             if os.path.exists('/proc/%s/stat' % pid):
                 try:
                     l=open('/proc/%s/stat' % pid).read().split()
                     uid=os.stat('/proc/%s/stat' % pid)[4]
                     swappercent1=0.0
                     rampercent1=0.0
                     #read the memory information
                     VMsize=0
                     RSS=0
                     #read the memory information
                     if not self.val.has_key(pid):
                        tempd=open('/proc/%s/cmdline' % pid)
                        tempvar=tempd.read()
                        tempd.close()
                        tempvar=re.sub(r'\s','%',tempvar)
                        tempvar=re.sub(r'\x00','%',tempvar)
                        tempvar=re.sub(r':','%',tempvar)
                        self.processargs[pid]=tempvar
                        if len(tempvar)==0:
                           continue


                     for memline in  open('/proc/%s/status' % pid).readlines():
                         l=memline.split()
                         if len(l) < 2: continue
                         name = l[0].split(':')[0]
                         if name=='VmSize': VMsize=long(l[1]) * 1024
                         if name=='VmRSS' : RSS=long(l[1]) * 1024
                         #if VMsize!=0 and RSS!=0: break
                    #print 'ram used%d swapused %d'%(RSS,VMsize-RSS)
                     swappercent1=100.0*(VMsize-RSS)/self.swaptotal
                     rampercent1=100.0*(RSS)/self.ramtotal
                     #print 'pid:%s cn2:%d'%(pid,self.cn2[pid])
                     if self.swappercent.has_key(pid):
                        if (swappercent1 < self.swappercent[pid]) and ((self.swappercent[pid]-swappercent1)> self.downdeadband[1]):
                           self.swappercent[pid]=swappercent1
                           output1=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor[1]+':'+self.device[1]+':'+self.valuetype+':'+ self.count[1]+':'+self.devinst[1]+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(swappercent1,3))
                           log(output1)
                        elif (swappercent1 > self.swappercent[pid]) and ((swappercent1 -self.swappercent[pid])> self.updeadband[1]):
                           self.swappercent[pid]=swappercent1
                           output1=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor[1]+':'+self.device[1]+':'+self.valuetype+':'+ self.count[1]+':'+self.devinst[1]+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(swappercent1,3))
                           log(output1)
                     else:
                          #print '%s found for first time'%pid
                          self.swappercent[pid]=swappercent1
                          output1=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor[1]+':'+self.device[1]+':'+self.valuetype+':'+ self.count[1]+':'+self.devinst[1]+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(swappercent1,3))
                          log(output1)
                     if self.rampercent.has_key(pid):
                        if (rampercent1 < self.rampercent[pid]) and ((self.rampercent[pid]-rampercent1)> self.downdeadband[0]):
                           self.rampercent[pid]=rampercent1
                           output1=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor[0]+':'+self.device[0]+':'+self.valuetype+':'+ self.count[0]+':'+self.devinst[0]+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(rampercent1,3))
                           log(output1)
                        elif (rampercent1 > self.rampercent[pid]) and ((rampercent1 - self.rampercent[pid])> self.updeadband[0]):
                           self.rampercent[pid]=rampercent1
                           output1=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor[0]+':'+self.device[0]+':'+self.valuetype+':'+ self.count[0]+':'+self.devinst[0]+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(rampercent1,3))
                           log(output1)
                     else:
                          #print '%s found for first time'%pid
                          self.rampercent[pid]=rampercent1
                          output1=self.protocolversion+':'+timestamp+':'+self.nodename+':'+self.sensor[0]+':'+self.device[0]+':'+self.valuetype+':'+ self.count[0]+':'+self.devinst[0]+':'+str(pid)+':'+str(uid)+':'+self.processargs[pid]+':'+str(round(rampercent1,3))
                          log(output1)


                 except:
                     traceback.print_exc(file=sys.stdout)
                     print sys.exc_info()


          if self.statusCounter==5:
             self.statusCounter=0
             try:
                 self.status.store(open(self.statusFileName,'w'))
             except:
                 traceback.print_exc(file=sys.stdout)
                 print sys.exc_info()
sensors['Sensors_Utilization_RamSwap_Processrecord']= Sensors_Utilization_RamSwap_Processrecord()

#







