'''Sensor Names Deadband
UtilizationDiskpartitionScalar  5
FanspeedCpuScalar               10
FanspeedMotherboardScalar       10
TempCpuScalar                   2
TempMotherboardScalar           2
UtilizationAggregatecpuScalar   7
UtilizationCpuProcessrecord     7
UtilizationRamScalar            7
UtilizationRamProcessrecord     7
UtilizationSwapProcessrecord    7
UtilizationSwapScalar           7
VoltageCpuScalar                1
VoltageMotherboardScalar        1
'''

import re
import sys
import gzip

if __name__=='__main__':
   if len(sys.argv) < 2:
      print "python Usage HealthMessageCleanUpScript <source1> <source2> ..."
      print "Note source file can be gzipped i.e. health.1.gz or uncompressed"
      print "Destination file is ConsolidatedHealthMessages.log.gz - yes it compresses"
      sys.exit(0)
   Deadbanddict={}
   #create the dictionary
   Deadbanddict['UtilizationDiskpartitionScalar']=5
   Deadbanddict['FanspeedCpuScalar']=10
   Deadbanddict['FanspeedMotherboardScalar']=10
   Deadbanddict['TempCpuScalar']=2
   Deadbanddict['TempMotherboardScalar']=2
   Deadbanddict['UtilizationAggregatecpuScalar']=7
   Deadbanddict['UtilizationCpuProcessrecord']=7
   Deadbanddict['UtilizationRamScalar']=7
   Deadbanddict['UtilizationRamProcessrecord']=7
   Deadbanddict['UtilizationSwapProcessrecord']=7
   Deadbanddict['UtilizationSwapScalar']=7
   Deadbanddict['VoltageCpuScalar']=1
   Deadbanddict['VoltageMotherboardScalar']=1

   CurrentState={}     #CurrentStateDictionary
   errorFile=gzip.GzipFile("error.log.gz",'a')
   ignoredLinesFile=gzip.GzipFile("ignoredHealth.log.gz",'a')
   outputFile=gzip.GzipFile("ConsolidatedHealthMessages.log.gz",'a')
   FileNameDict={}
   for filename in sys.argv[1:]:
       if len(filename)>3 and filename[len(filename)-3:]==".gz":
           healthFile=gzip.GzipFile(filename,'r')
       else:
           healthFile=open(filename,'r')
       l=healthFile.readline()
       while 'HEALTH' not in l:
         l=healthFile.readline()
       if 'HEALTH' in l:
         x=l.split()
         payload=x[5]
         temp=payload.split(':')
         FileNameDict[filename]=float(temp[1])
         healthFile.seek(0)
         healthFile.close()

   items=FileNameDict.items()
   backitems=[ [v[1],v[0]] for v in items]
   backitems.sort()
   #print backitems
   SortedFileNames=[ backitems[i][1] for i in range(0,len(backitems))]
   #print SortedFileNames


   for filename in SortedFileNames:
       if len(filename)>3 and filename[len(filename)-3:]==".gz":
           healthFile=gzip.GzipFile(filename,'r')
       else:
           healthFile=open(filename,'r')
       for line in healthFile:
           try:
             if not 'HEALTH' in line:
               errorFile.write(line)
               continue
             x=line.split()
             payload=x[5]
             temp=payload.split(':')
             DeadbanddictEntry=temp[3]+temp[4]+temp[5]
             if temp[5]=="Scalar":
                CurrentStateEntry=temp[2]+temp[3]+temp[4]+temp[5]+temp[7]
                currentValue=float(temp[8])
                if CurrentState.has_key(CurrentStateEntry):
                   if (abs(currentValue - CurrentState[CurrentStateEntry])>=float(Deadbanddict[DeadbanddictEntry])):
                      CurrentState[CurrentStateEntry]= currentValue
                      outputFile.write(line)
                   else:
                      ignoredLinesFile.write(line)
                else:
                      CurrentState[CurrentStateEntry]= currentValue
                      outputFile.write(line)
             elif temp[5]=="Processrecord" :
                CurrentStateEntry=temp[2]+temp[3]+temp[4]+temp[5]+temp[7]+temp[8]+temp[9]+temp[10]
                currentValue=float(temp[11])
                processName=temp[10]
                #if the name of process is blank ignore it
                if len(processName) == 0:
                   ignoredLinesFile.write(line)
                   continue

                if CurrentState.has_key(CurrentStateEntry):
                   if (abs(currentValue - CurrentState[CurrentStateEntry])>=float(Deadbanddict[DeadbanddictEntry])):
                      CurrentState[CurrentStateEntry]= currentValue
                      outputFile.write(line)
                   else:
                      ignoredLinesFile.write(line)
                else:
                      CurrentState[CurrentStateEntry]= currentValue
                      outputFile.write(line)
           except:
                errorFile.write("error in filename:"+filename+" ")
                errorFile.write(sys.exc_info())
                #errorFile.write('\n')
                errorFile.write(line)
                continue

       healthFile.close()
   errorFile.close()
   ignoredLinesFile.close()
          