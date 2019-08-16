
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
readacct = os.path.dirname(sys.argv[0]) + '/../acct/read_acct'

sample = "Nov 28 11:24:20 whcdf03 HEALTH:"

def build_message(recs):
    count = len(recs)
    ts = int(time.time())
    # protocol version and header building should be part of
    # the message sending library!
    header = "1.0:%s:%s:Accounting:Cmds:Death:%d"%(ts,nodename,count)
    # each rec will always appear to come from devinst = 0
    newrecs = ["0:%s"%string.join(i,':') for i in recs]
    recdata = string.join(newrecs,':')
    return "%s:%s"%(header,recdata)

def send_syslog(recs):
    msg = build_message(recs)
    syslog.syslog(prio,msg)

def send_console(recs):
    msg = build_message(recs)
    print sample,msg

send = send_syslog

def run(filename, offset, fullsave):
    tmpfile = '/tmp/t' + "%s"%os.getpid() + '.txt'
    arg_offset = ''
    if offset>0: arg_offset = "-s %d"%offset
    args = "%s -f %s -r %s %s"%(readacct,filename,fullsave,arg_offset)

    # print >>sys.stderr,"running %s"%args
    # run the command
    x = os.popen3(args)
    count = 0
    recs = []

    for line in x[1]:
        s = line.split()
        #         host = s[0]
        #         cmd = s[1]
        #         rc = s[2]
        #         stime = s[3]
        #         etime = s[4]
        #         aver_mem = s[5]
        #         sig = s[6]
        # print line

        recs.append(s[0:7])

        count += 1
        if count % 25 == 0:
            send(recs)
            recs = []

    # read error info
    err = x[2].read()
    if len(err) > 10: print err
        
    if len(recs) > 0: send(recs)
    
import glob
import stat

class AcctFile:
    def __init__(me,mtime,name):
        me.offset=0
        me.mtime=mtime
        me.filename=name

    def __cmp__(me,other):
        r = cmp(other.mtime,me.mtime)
        if r==0: return cmp(me.filename,other.filename)
        return r

    def __str__(me): return "%d-%s"%(me.mtime,me.filename)

    def __repr(me): return me.__str__()

    def is_gz(me): return me.filename.endswith('gz')

def get_files(pattern):
    flist = glob.glob(pattern)
    files = []
    for n in flist:
        files.append( AcctFile(int(os.stat(n)[stat.ST_MTIME]),n) )

    files.sort()
    # for n in files: print n
    # files.sort(cmp=lambda x,y: cmp(x[1],y[1]))
    # fix the dates
    for n in zip(files[0:-1],files[1:]):
        if n[0].is_gz(): n[0].mtime = n[1].mtime
    files.sort()
    return files

def run_matches(pattern, fullsave):
    files = get_files(pattern)

    files.reverse()
    for n in files:
        run(n.filename,0,fullsave)

def get_file_set(pattern, fullsave):
    files = get_files(pattern)
    
    # read in old location information
    old_mtime = 0
    old_offset = 0
    s = os.stat(fullsave)
    mode = s[stat.ST_MODE]

    if stat.S_ISREG(mode)==False:
        raise NameError,"the save file is not a file"

    line = file(fullsave,'r').read().strip().split()
    old_mtime = int(line[0])  # signed/unsigned?
    old_offset = int(line[1]) # 32 bit int here?

    # remove files older than the given date
    files.pop()
    while files[-1].mtime < old_mtime: files.pop()
    files[-1].offset = old_offset    

    last = files[-1]
    if not last.filename.endswith('gz') and last.offset >= os.stat(last.filename)[stat.ST_SIZE]:
        files.pop()

    files.reverse()
    return files

def run_all(save_path, filename, offset, pattern):
    # there must not be a saved position file if there is a filename given
    fullsave = None
    if save_path:
        fullsave = save_path + "/acctlogger_last_position.txt"
        if os.access(save_path,os.F_OK)==False:
            raise NameError,"no save path dir given: %s"%save_path

    # check if we are given a filename and have an existing position file
    if filename and fullsave and os.access(fullsave,os.F_OK)==True:
        raise NameError,"both position file found and filename given"
    
    if filename:
        run(filename,offset,fullsave)
    elif os.access(fullsave,os.F_OK)==False:
        run_matches(pattern,fullsave)        
    else:
        files = get_file_set(pattern,fullsave)
        for n in files: run(n.filename,n.offset,fullsave)        
        

def checkCacheDir(path):
    if os.access(path,os.F_OK)==False:
        os.mkdir(path)

if __name__ == '__main__':

    arglen = len(sys.argv)
    if arglen < 2:
        print "Usage: ",sys.argv[0]," [-c] [-p savepos_path] [-f filename] [-o offset_in_file] [-r file_pattern]"
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
        print "\nThe file_pattern should include the full path and the beginning part of the file names."
        sys.exit(-1)

    prog = sys.argv.pop(0)
    optslist,args = getopt.getopt(sys.argv,'tcp:f:o:r:')
    dopts = dict(optslist)
    
    save_path = None
    filename = None
    offset = 0

    if dopts.has_key("-c"):
        send = send_console
        print "logging to console"
    elif dopts.has_key("-t"):
        print "logging to test syslog"
	prio=syslog.LOG_DEBUG
        syslog.openlog('HEALTH',syslog.LOG_NOWAIT,syslog.LOG_USER)
    else:
        syslog.openlog('HEALTH',syslog.LOG_NOWAIT,syslog.LOG_USER)

    if dopts.has_key("-p"):
        save_path = dopts["-p"]
        checkCacheDir(save_path)

    if dopts.has_key("-f"):
        filename = dopts["-f"]
        if dopts.has_key("-o"):
            offset = int(dopts["-o"])

    if dopts.has_key("-r"):
        pattern = dopts["-r"] + '*'

    run_all(save_path,filename,offset,pattern)
