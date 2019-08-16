import sys
import os
import time
import re
import glob

class LastPos:
    '''File holds a tuple (file_name, inode_num, offset) for each file
    we are processing or should process.  It also has a header that
    contains (last_completion_time, target_dir, file_pattern).
    If files are compressed, the recorded offset is assumed to be an
    offset from the start of the uncompressed file.
    
    target_dir: the place where the files to be checked are kept
    app_name: the name given to the last position save file
    dir_name: the place where the last position save file will go
    file_pattern: glob pattern for files to check in target_dir'''
    
    tformat = "%20.20d\n"
    
    def __init__(me,dir_name,app_name,target_dir,file_pattern):
        me.target_dir = target_dir
        me.pat = file_pattern
        me.last_time = 0
        me.file_name = dir_name + '/' + app_name
        me.tmp_name = me.file_name + '_tmp'
        me.entries = []

        if os.access(me.tmp_name, os.F_OK):
            # yuck - we have a have-written status file
            # what do we do now?
            print "LastPos: there exists a half-written position file ",me.tmp_name
            print "deleting the half-written one and using the original"
            os.remove(me.tmp_name)
            # os.rename(me.tmp_name,me.file_name)

        make_new = 0
        # if there is a file, read its contents
        if os.access(me.file_name, os.R_OK):
            try:
                f = open(me.file_name,'r')
                last_time, me.target_dir, me.pat = f.readline().split()
                me.last_time=int(last_time)
                for entry in f:
                    me.entries.append(entry.split())
            except ValueError:
                make_new = 1
        else:
            make_new = 1

        # I think that each file entry should be maintained with a last-
        # completion timestamp and the other information now in the header.

        # I could read the old set of files, then build a new set using the
        # new information from the file system, then
        # start producing new entries into the output file (tmp one?) as
        # the application says it has made progress on it (entry by entry)
        # I will flush the file so entries in the tmp file are always
        # complete and valid.

        # Get the new list of files of file system
        # this is the list of files >= last completion time
        # Clean up current list using new file list
        # the clean-up means getting rid of files that have not been written
        # to since the last completion time
        # Fix file names using inode information
        # the fix is tricky - we must assume that the file has been
        # (a) renamed (retains inode), or
        # (b) compressed and given an older generation number (different inode)

        if make_new:
            # write everything to the tmp_name, then rename to file_name?
            open(me.file_name,'w').write(LastTimeCompleted.tformat%me.last_time)

    def lastCompletedTask(me):
        '''Use this to find the last time the task was completed'''
        return me.last_time

    def taskCompleted(me):
        '''Use this to mark the successful completion of a task'''
        t = int(time.time())
        os.rename(me.file_name,me.tmp_name)
        open(me.file_name,'w').write(LastTimeCompleted.tformat%t)
        os.remove(me.tmp_name)
        me.last_time = t
    
def test_completed(iter):
    print "Test iter %s"%iter
    tc = LastTimeCompleted(sys.argv[1],sys.argv[2])
    for i in range(0,6):
        time.sleep(2)
        tc.taskCompleted()
        print tc.lastCompletedTask()
    	    

# test program idea:
# generator - writes data to an output file every second, then
# starts a new file every 20 seconds.
# reader1 - picks up new data from the files every 9 seconds
# reader2 - picks up new data from the files every 25 seconds

# the completion time per file is essential to present older,
# unprocessed files from being removed from the list.

import thread
import random
from threading import Thread

fmat_seq = "lastpos_testfile.%d"
fmat_one = "lastpos_testfile.1"

class Gener(Thread):
    def __init__(me,total_files, seconds_between_write):
        Thread.__init__(me)
        me.tot=total_files
        me.secs=seconds_between_write

    def rename_files(me,seq):
        for i in range(seq,0,-1):
            #print fmat_seq%i,fmat_seq%(i+1)
            os.rename(fmat_seq%i,fmat_seq%(i+1))

    def run(me):
        seq = 1
        curr = open(fmat_one,'w')
        x = 0
        while seq<me.tot:
            # add data
            x += 1
            curr.write("test"*random.randint(5,100))
            curr.flush()
            # move to next file if necessary
            if x % me.secs == 0:
                curr.close()
                me.rename_files(seq)
                seq += 1
                curr = open(fmat_one,'w')
            time.sleep(1)
                

class Reader(Thread):
    def __init__(me,seconds_between_check):
        Thread.__init__(me)
        me.secs = seconds_between_check
        #me.last = LastPos()

    def run(me):
        pass

def testit():
    workers = [Gener(5,10),Reader(4),Reader(15)]
    map(lambda (x): x.start(),workers)
    map(lambda (x): x.join(),workers)

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print "usage: %s "%sys.argv[0]
        sys.exit(1)

    sys.exit(testit())

