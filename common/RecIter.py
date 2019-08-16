
import sys
import os
import re
import datetime
import time
import os.path

timeexp = re.compile("(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+)")
clustexp = re.compile("([a-zA-Z]+).*")

class NodeSel:
    def __init__(me):
        me.ex = re.compile("(([a-zA-Z0-9]+)/0)\+*")

    def getNodes(me,st):
        return [m.group(2) for m in me.ex.finditer(st)]

# ----------------------

def toSeconds(st):
    s = st.split(':')
    return str(int(s[0])*60*60 + int(s[1])*60 + int(s[2]))

def toNetType(st):
    s = st.split(':')
    if len(s) <= 1: return "none"
    else: return s[1]

def extractCluster(st):
    return clustexp.match(st).group(1)

# -----------------------

class Header:

    # unfortunately we need to use information in the data
    # to ensure a unique job ID number here
    # each node where a scheduler runs needs an entry
    offset_table = {
        'dellquad2':12000000,'lqcd':0,'kaon2':4000000,'kaon1':3000000
        }
    def __init__(me,rectime, rectype, recjob):
        me.rectime = me.toTime(rectime) # get time
        me.rectype = rectype
        recid,recnode = me.convertID(recjob)
        me.recnode = recnode
        me.recid = str(int(recid) + Header.offset_table[me.recnode]) + str(me.year)[2:] # I have added year to the offset

    def toTime(me,st):
        d,t = st.split(' ')
        df = [ int(i) for i in d.split('/')]
        # added an year so that it can be added to the recid to make it unique across years
        me.year=df[2]
        tf = [ int(i) for i in t.split(':')]
        return time.mktime(datetime.datetime(df[2],df[0],df[1],tf[0],tf[1],tf[2]).timetuple())

    def convertID(me,st):
        return st.split('.',2)[0:2]

    def getAttrs(me):
        m={}
        m['recid'] = me.recid
        m['recnode'] = me.recnode
        m['rectype'] = me.rectype
        m['rectime'] = me.rectime
        return m
   
# -----------------------

class NoFileError(Exception):
    def __init__(me):
        pass
    def __str__(me):
        return "No active file"

import stat

class FileProcessor:
    """if given a list of (file,offset), it will process each file starting
    at the next record after offset (offset points to the last successfully
    processed record start.
    If given nothing, then it will open the current directory and
    process all the files in it that start with the number 2. The
    offset will be assumed to be zero."""

    def __init__(me,filename=None,offset=0):
        me.filelist = []
        if filename:
            me.curr_ctime = os.stat(filename)[stat.ST_MTIME]
        else:
            me.curr_ctime = 0
        me.curr_file = None
        me.curr_pos = 0
        me.select_nodes = NodeSel()
        me.counts = { 'E':0, 'S':0, 'Q':0, 'D':0, 'R':0, 'T':0, 'A':0 }
        me.table = { 'E':me.adjustE, 'S':me.adjustS, 'D':me.adjustD, 'Q':me.adjustQ }
        if filename==None:
            for f in os.listdir("."):
                if f[0]!='2': continue
                me.filelist.append(tuple([f,0]))
                #print f
        else:
            me.filelist.append(tuple([filename,offset]))

    def getAttributes(me,header,recin):
        m = { }
        rec = recin.split(' ')
        c = 0

        for f in rec:
            s = f.split('=',1)
            if len(s)!=2: continue
            m[s[0]]=s[1]

        return me.table[header.rectype](header,m)

    def adjustS(me,header,attrs):
        m = header.getAttrs()
        if not attrs.has_key('qtime'): return None
        if not attrs.has_key('start'): return None
        if not attrs.has_key('etime'): return None
        if not attrs.has_key('user'): return None
        if not attrs.has_key('jobname'): return None
        if not attrs.has_key('queue'): return None
      #  if not attrs.has_key('account'): return None
        if not attrs.has_key('group'): return None
        if not attrs.has_key('Resource_List.nodes'): return None
        if not attrs.has_key('Resource_List.nodect'): return None
        if not attrs.has_key('exec_host'): return None
        # Checking complete
        m['birth'] = attrs['qtime']
        m['start'] = attrs['start']
        m['end'] = attrs['etime']
        m['user'] = attrs['user']
        m['jobname'] = attrs['jobname']
        m['queue'] = attrs['queue']
        m['account'] = attrs.get('account','none')
        m['grp'] = attrs['group']
        #print header.recid,header.rectype
        #if not attrs.has_key('Resource_List.nodes'): return None
        m['nettype'] = toNetType(attrs['Resource_List.nodes'])
        m['nodecount'] = attrs['Resource_List.nodect']
        m['nodelist'] = me.select_nodes.getNodes(attrs['exec_host'])
        m['clust'] = extractCluster(attrs['exec_host'])
        return m

    def adjustQ(me,header,attrs):
        m = header.getAttrs()
        if not attrs.has_key('queue'): return None
        m['queue'] = attrs['queue']
        return m

    def adjustD(me,header,attrs):
        m = header.getAttrs()
        if not attrs.has_key('requestor'): return None
        m['requestor'] = attrs['requestor']
        return m

    def adjustE(me,header,attrs):

        m = header.getAttrs()
        if not attrs.has_key('Resource_List.nodes'): return None
        if not attrs.has_key('qtime'): return None
        if not attrs.has_key('start'): return None
        if not attrs.has_key('end'): return None
        if not attrs.has_key('user'): return None
        if not attrs.has_key('jobname'): return None
        if not attrs.has_key('queue'): return None
        if not attrs.has_key('group'): return None
        if not attrs.has_key('Resource_List.nodect'): return None
        if not attrs.has_key('exec_host'): return None
        if not attrs.has_key('Exit_status'): return None
       
        ####
        m['birth'] = attrs['qtime']
        m['start'] = attrs['start']
        m['end'] = attrs['end']

        m['user'] = attrs['user']
        m['jobname'] = attrs['jobname']
        m['queue'] = attrs['queue']
        m['account'] = attrs.get('account','none')
        m['grp'] = attrs['group']
        m['nettype'] = toNetType(attrs['Resource_List.nodes'])

        m['nodecount'] = attrs['Resource_List.nodect']
        m['nodelist'] = me.select_nodes.getNodes(attrs['exec_host'])
        m['clust'] = extractCluster(attrs['exec_host'])

        m['rc'] = attrs['Exit_status']
        m['vmem'] = attrs.get('resources_used.vmem','0kb')[:-2]
        m['mem'] = attrs.get('resources_used.mem','0kb')[:-2]
        m['cput'] = toSeconds(attrs.get('resources_used.cput','0:0:0'))
        m['walltime'] = toSeconds(attrs.get('resources_used.walltime','0:0:0'))
        return m

    def processRecord(me,rec):
        if rec[0] == '\x00': return None
        s=rec.split(';')
        if len(s)<2: return None
        if s[1] == 'T': return None
        if s[1] == 'R': return None
        if s[1] == 'A': return None

        try:
            head = Header(s[0],s[1],s[2])
            recattr = me.getAttributes(head,s[3])
            me.counts[ s[1] ] += 1
            return recattr
        except Exception,inst:
            return None

    def checkpointData(me):
        if me.curr_file == None: raise NoActiveFile()
        return (me.curr_ctime,me.curr_file,me.curr_pos)

    def printSummary(me):
        print me.counts

    def records(me):
        for fn in me.filelist:
            # print fn
            me.curr_pos = fn[1]
            me.curr_file = fn[0]
            file_fn = open(me.curr_file,'r')
            file_fn.seek(me.curr_pos)

            # skip the current record 
            for rec in file_fn:
                reclen = len(rec)
                # checkpoint - record the last retrieved record
                me.curr_pos += reclen
                recattr = me.processRecord(rec)
                if recattr == None: continue
                # add an attribute that indicates the record size in bytes
                recattr['recsize'] = reclen
                yield recattr
                

# -------------------- testing and main below --------------------

test_caseE = """03/27/2006 00:00:02;E;32461.kaon1.fnal.gov;user=simone group=g038 account=fermimilcheavylight jobname=hQ_1S queue=workq ctime=1143430664 qtime=1143430665 etime=1143430665 start=1143437662 exec_host=qcd0701/0+qcd0702/0+qcd0703/0+qcd0704/0+qcd0705/0+qcd0706/0+qcd0707/0+qcd0708/0+qcd0709/0+qcd0710/0+qcd0711/0+qcd0712/0+qcd0713/0+qcd0801/0+qcd0805/0+qcd0806/0 Resource_List.neednodes=16:myrinet Resource_List.nodect=16 Resource_List.nodes=16:myrinet Resource_List.walltime=02:00:00 session=0 end=1143439202 Exit_status=0 resources_used.cput=00:00:18 resources_used.mem=22960kb resources_used.vmem=63604kb resources_used.walltime=00:25:09"""

test_caseS = """09/16/2006 00:33:04;S;159836.lqcd.fnal.gov;user=rtevans group=lqcd account=fermimilcheavylight jobname=twopt queue=workq ctime=1158384782 qtime=1158384782 etime=1158384782 start=1158384784 exec_host=pion1112/0+pion1113/0+pion1114/0+pion1119/0+pion1120/0+pion1122/0+pion1123/0+pion1124/0 Resource_List.neednodes=pion1112+pion1113+pion1114+pion1119+pion1120+pion1122+pion1123+pion1124 Resource_List.nodect=8 Resource_List.nodes=8 Resource_List.walltime=00:20:00"""

test_caseQ = """09/16/2006 00:34:27;Q;159837.lqcd.fnal.gov;queue=workq"""

test_caseD = """09/16/2006 00:33:04;D;159489.lqcd.fnal.gov;requestor=root@lqcd.fnal.gov"""

def printMap(m):
    print '------------------------'
    for i in m.items():
        print i[0],' = ',i[1]

def runTest(fp):
    tests = [ test_caseE, test_caseD, test_caseQ, test_caseS ]
    for i in tests:
        x = fp.processRecord(i)
        printMap(x)

def run(fp):
    for r in fp.records():
        print "------------"
        print r

if __name__ == '__main__':
    fl = sys.argv[1:]
    fp = FileProcessor(fl)
    
    if len(sys.argv) == 2 and sys.argv[1] == 'T':
        runTest(fp)
    else:
        run(fp)

    print fp.printSummary()
