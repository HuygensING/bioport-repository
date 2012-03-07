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
#    raise ValueError("no valid DSN found")

DB_CONNECTION = DSN = _find_valid_dsn()

