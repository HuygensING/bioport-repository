##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gerbrandy S.R.L.
# 
# This file is part of bioport.
# 
# bioport is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/gpl-3.0.html>.
##########################################################################

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
    DSN = None


THIS_DIR = os.path.split(os.path.abspath(__file__))[0]
SVN_REPOSITORY  = os.path.abspath(os.path.join(THIS_DIR, 'data/bioport_repository'))
SVN_REPOSITORY_LOCAL_COPY = os.path.abspath(os.path.join(THIS_DIR, 'data/bioport_repository_local_copy'))
IMAGES_CACHE_LOCAL = os.path.join(THIS_DIR, 'tmp')
SQLDUMP_FILENAME = os.path.join(THIS_DIR, 'data/bioport_mysqldump.sql')
CREATE_NEW_DUMPFILE = False #very expesnive if True