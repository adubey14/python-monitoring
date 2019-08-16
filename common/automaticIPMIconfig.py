import commands
import os
from string import Template

def config(Sdrname,EntityName,IdentifierName):
   IPMICommandTemplate=Template('ipmitool -S ${sdrstring} sdr entity \"${query}\"')
   if not os.path.exists(Sdrname):
      commands.getstatusoutput('ipmitool sdr dump %s'%Sdrname)

   try:
       outputlist=commands.getoutput(IPMICommandTemplate.substitute(sdrstring=Sdrname,query=EntityName)).split('\n')
   except Exception, e:
       print sys.exc_info()
       outputlist=[] #send nothing. This will disable the sensor

   returnlist=[]
   for element in outputlist:
       if  IdentifierName in element:
           returnlist.append(element.split('|')[0].strip())
   return returnlist




