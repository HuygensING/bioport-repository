import os
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine

DB_NAME = 'bioport_test'
POSSIBLE_DSN = ['mysql://root@localhost/%s' % DB_NAME,
                'mysql://jge:MilanO8@localhost/%s' % DB_NAME,
                'mysql://localhost/%s' % DB_NAME,
               ]


def _find_valid_dsn():
    for s in POSSIBLE_DSN:
        try:
            create_engine(s).connect()
        except OperationalError:
            pass
        else:
            return s
    raise ValueError("no valid DSN found")

try:
    DB_CONNECTION = DSN = _find_valid_dsn()
except ValueError:
    print 'NO VALID DSN FOUND IN TEST CONFIG'


THIS_DIR = os.path.split(os.path.abspath(__file__))[0]
SVN_REPOSITORY  = os.path.abspath(os.path.join(THIS_DIR, 'data/bioport_repository'))
SVN_REPOSITORY_LOCAL_COPY = os.path.abspath(os.path.join(THIS_DIR, 'data/bioport_repository_local_copy'))
IMAGES_CACHE_LOCAL = os.path.join(THIS_DIR, 'tmp')
SQLDUMP_FILENAME = os.path.join(THIS_DIR, 'data/bioport_mysqldump.sql')
CREATE_NEW_DUMPFILE = False #very expesnive if True