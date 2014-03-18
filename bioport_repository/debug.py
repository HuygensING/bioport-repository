##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gebrandy S.R.L.
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

from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging
 
#logging.basicConfig()
#logger = logging.getLogger("myapp.sqltime")

logger = logging.getLogger('sql_debug')
logger.setLevel(logging.DEBUG)
queries = []

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, 
                        parameters, context, executemany):
    context._query_start_time = time.time()
    logger.debug("Start Query: %s (%s)" % (statement, parameters))
    
@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, 
                        parameters, context, executemany):
    total = time.time() - context._query_start_time
    logger.debug("Query Complete. Total Time: %f" % total)
    global queries 
    queries.append((total, statement, parameters))
    queries.sort()
    queries.reverse()
#    logger.debug('longest:')
#    for total, statement, parameters in queries[:5]:
#        print total, statement, parameters 
    logger.debug("Total Queries: %s" % len(queries))
