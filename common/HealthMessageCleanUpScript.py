import re
import sys
import string

def fix(file_name):
   fileout = open(file_name+'.fixed','w')
   infile  = open(file_name,'r')
   
   for line in infile:
         if 'Worker_Node' in line: continue
         if 'HEALTH' in line:
            x=line.split()
            payload=x[5]
            temp=payload.split(':')
            if temp[0]!='1.0':
               payload='1.0:'+payload
            payload=re.sub(r':t:Swap:',':Utilization:Swap:',payload)
            payload=re.sub(r':U:Ram:',':Utilization:Ram:',payload)
            x[5]=payload
            x=string.join(x)
            fileout.write(x+'\n')
         else: continue


def split(file_name):
   max_bytes = 300000000
   infile = None
   if file_name == '-':
	infile = sys.stdin
        file_name = "stdin"
   else:
        infile  = open(file_name,'r')
   ext_count = 1
   byte_count = max_bytes + 1
   outfile = None

   for line in infile:

      if byte_count > max_bytes:
         outfile = open( "%s.g%d"%(file_name,ext_count), 'w')
         ext_count += 1
         byte_count = 0

      outfile.write(line)
      byte_count += len(line)
   

if __name__=='__main__':
   if len(sys.argv) < 3:
      print "python Usage %s fix|split <source_file_name>"%sys.argv[0]
      sys.exit(1)

   if sys.argv[1] == 'fix':
      fix(sys.argv[2])
   elif sys.argv[1] == 'split':
      split(sys.argv[2])
   else:
      print "no such function: %s"%sys.argv[1]
      sys.exit(1)
   

