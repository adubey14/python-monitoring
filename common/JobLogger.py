
import RecIter
import sys
import base64
import string
import zlib
import time
import os
import syslog
import getopt

nodename = os.uname()[1]
prio = syslog.LOG_NOTICE

sample = "Nov 28 11:24:20 whcdf03 JOBSDATA:"

def build_message(recs):
    count = len(recs)
    ts = int(time.time())
    # protocol version and header building should be part of the message sending library!
    header = "1.0:%s:%s:Batch:Pbs:Job:%d"%(ts,nodename,count)
    # each rec will always appear to come from devinst = 0
    recdata = string.join(["0:%s"%i for i in recs],':')
    return "%s:%s"%(header,recdata)

def send_syslog(recs):
    msg = build_message(recs)
    syslog.syslog(prio,msg)

def send_console(recs):
    msg = build_message(recs)
    print sample,msg

send = send_syslog

def run(fp,fullsave):
    count = 0
    total = 0
    totalbytes = 0
    recs = []

    for i in fp.records():
        # The only list we have is the nodelist.
        # This needs to be converted to something printable if it is present.
        if i.has_key('nodelist'):
            tmp = i['nodelist']
            i['nodelist'] = string.join(tmp,'~')
        # convert dictionary to name/value pairs
        newrec=base64.b64encode(zlib.compress(string.join(["%s=%s"%r for r in i.iteritems()])))
        recs.append(newrec)
        count += 1
        totalbytes += len(newrec)
        if totalbytes > 1024:
            send(recs)
            total += 1
            recs = []

    if len(recs) > 0:
        send(recs)
        total += 1

    # get the checkpointing data from fp (create_time, file_name, offset)
    ctime,fname,offset = fp.checkpointData()
    # save the information if asked to do so
    if fullsave: file(fullsave,'w').write("%d %s %d"%(ctime,fname,offset))
    return total,count

import stat

class JobFile:
    def __init__(me,mtime,name):
        me.offset=0
        me.mtime=mtime
        me.filename=name

    def __cmp__(me,other):
        r = cmp(me.mtime, other.mtime)
        if r==0: return cmp(me.filename,other.filename)
        return r

    def __str__(me): return "%d-%s"%(me.mtime,me.filename)

    def __repr(me): return me.__str__()

    def is_gz(me): return me.filename.endswith('gz')

def find_new_files(old_filename, mtime):
        # find any new files that appeared
        dlist = os.listdir('.')
        rest = []
        for n in dlist:
            info = os.stat(n)[stat.ST_MTIME]
            if n!=old_filename and info>=mtime and n[0]=='2':
                rest.append(JobFile(info,n))

        rest.sort()
        return rest
    
def run_all(save_path, filename, offset):
    # there must not be a saved position file if there is a filename given
    fullsave = None
    if save_path:
        fullsave = save_path + "/joblogger_last_position.txt"
        if os.access(save_path,os.F_OK)==False:
            raise NameError,"no save path dir given: %s"%save_path

    # check if we are given a filename and have an existing position file
    if filename and fullsave and os.access(fullsave,os.F_OK)==True:
        raise NameError,"both position file found and filename given"
    
    if filename:
        fp = RecIter.FileProcessor(filename,offset)
        tot,rcnt = run(fp,fullsave)
        # print "Done with ",filename," total = ",tot," count = ",rcnt
	# print "counts = ",fp.printSummary()
    elif os.access(fullsave,os.F_OK)==False:
        rest = find_new_files(None,0)
	firsttime=True
        for n in rest:
            if firsttime:
	        firsttime=False
            else:
                time.sleep(3*60)
            fp = RecIter.FileProcessor(n.filename,0)
            tot = run(fp,fullsave)        
    else:    
        old_mtime = 0
        old_filename = None
        old_offset = 0
        s = os.stat(fullsave)
        mode = s[stat.ST_MODE]
        if stat.S_ISREG(mode)==False:
            raise NameError,"the save file is not a file"
        
        line = file(fullsave,'r').read().strip().split()
        old_mtime = int(line[0])  # signed/unsigned?
        old_filename = line[1]
        old_offset = int(line[2]) # 32 bit int here?
        s = os.stat(old_filename)
        size = s[stat.ST_SIZE]
        mtime = s[stat.ST_MTIME]

        # there is more data in the old file
        if old_offset < size:
            fp = RecIter.FileProcessor(old_filename,old_offset)
            run(fp,fullsave)

        rest = find_new_files(old_filename, mtime)

        for n in rest:
            fp = RecIter.FileProcessor(n.filename,0)
            run(fp,fullsave)
        
def checkCacheDir(path):
    if os.access(path,os.F_OK)==False:
        os.mkdir(path)


if __name__ == '__main__':
    arglen = len(sys.argv)
    if arglen < 2:
        print "Usage: ",sys.argv[0]," [-c] [-p savepos_path] [-f filename] [-o offset_in_file]"
        print "The savepos_path is the place where the last position information"
        print "file will be stored (this should be a directory)."
        print "The filename is a specific file to be read and processed\n"
        print "if a position save file is present in savepos_path, then"
        print "a filename may not be given.\n"
        print "if a savepos_path is given, but no position file is present"
        print "there, then all the files in the current directory will be"
        print "processed and a new position file will be written.\n"
        print "The -c option can be used to check the operation of this utilitity."
        print "Only printing to the console occurs with -c."
        print "\nIf you specify a filename, you can optionally specify a "
        print "starting position within that file."
        sys.exit(-1)

    prog = sys.argv.pop(0)
    optslist,args = getopt.getopt(sys.argv,'tcp:f:o:')
    dopts = dict(optslist)
    
    save_path = None
    filename = None
    offset = 0

    if dopts.has_key("-c"):
        send = send_console
        # print "logging to console"
    elif dopts.has_key("-t"):
        print "logging to test syslog"
	prio=syslog.LOG_DEBUG
        syslog.openlog('JOBSDATA',syslog.LOG_NOWAIT,syslog.LOG_USER)
    else:
        syslog.openlog('JOBSDATA',syslog.LOG_NOWAIT,syslog.LOG_USER)

    if dopts.has_key("-p"):
        save_path = dopts["-p"]
        checkCacheDir(save_path)

    if dopts.has_key("-f"):
        filename = dopts["-f"]
        if dopts.has_key("-o"):
            offset = int(dopts["-o"])

    run_all(save_path,filename,offset)
