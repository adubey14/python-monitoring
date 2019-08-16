
import sys
import yaml
import dbenv

def getMysqlURL(info):
    return "mysql://%(username)s:%(password)s@%(host)s/%(database)s"%info

def getSqliteURL(info):
    return "sqlite:///%(dbfile)s"%info

def readConfig(filename, entryname=dbenv.db_env):
    conf = yaml.load(open(filename))
    info = conf[entryname]
    adapter = info['adapter']
    if adapter == 'mysql': return getMysqlURL(info)
    elif adapter == 'sqlite3': return getSqliteURL(info)
    else:
    	raise Exception('unknown database adapter: %s, for database: %s'%(adapter,entryname))

class URLCache:
    def __init__(me,filename, entryname):
        me.cached = readConfig(filename, entryname)

    def getURL(me): return me.cached
        
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "usage: %s database_yml_file entry_name"%sys.argv[0]
        sys.exit(1)

	entry = dbenv.db_env
	if len(sys.argv) == 3: entry = sys.argv[2]

    url = readConfig(sys.argv[1], entry)
    print url
