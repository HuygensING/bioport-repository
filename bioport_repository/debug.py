from sqlalchemy.event import listen
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
    logger.debug("Start Query: %s" % statement)
    
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
