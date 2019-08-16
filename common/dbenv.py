
import sys
import os

'''You are expected to run this setup script from where it is
in the development/release directory structure.  It will set up
an import path for the rest of the scripts.'''

# sys.path.insert(0, '/path/to/development-release/tree')
db_env = os.getenv('RAILS_ENV')
if db_end == None: db_env = 'development'