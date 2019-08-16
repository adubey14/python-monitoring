
import sys
import os
import time

class LastTimeCompleted:
    '''Record the last time an application completed it task
    into file dir_name/app_name.  On construction, read the previous
    completed time.
    This should really add the last time the task
    was completed to the end of the file and use seek to locate the
    last entry.  A method such as this would allow a history of runs
    to be accumulated.'''
    
    tformat = "%20.20d\n"
    
    def __init__(me,dir_name,app_name):
        me.last_time = 0
        me.file_name = dir_name + '/' + app_name
        me.tmp_name = me.file_name + '_tmp'

        if os.access(me.tmp_name, os.F_OK):
            os.remove(me.file_name)
            os.rename(me.tmp_name,me.file_name)

        make_new = 0
        if os.access(me.file_name, os.R_OK):
            try:
                me.last_time = int(open(me.file_name, 'r').readline())
            except ValueError:
                make_new = 1
        else:
            make_new = 1

        if make_new:
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
    	    
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "usage: %s dirname appname"%sys.argv[0]
        sys.exit(1)

    test_completed(1)
    test_completed(2)
