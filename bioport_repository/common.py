class BioPortException(Exception):
    pass

class BioPortNotFoundError(Exception):
    pass
import datetime

def to_date(s, round='down' ):
    """Take a string in YYYY[-MM[-DD] format and return a date object
    
    round:
        one of ['down', 'up']: if 'down', take the lowest date, of 'up', take the max
        (i.e. to_date('2000', 'up') == datetime.datetime(2000, 1, 1))
        
    
    """
    if not s:
        return s
    if len(s) == 4:
        format = '%Y'
        result = datetime.datetime.strptime(s, format)
        if round == 'up':
            result = result.replace(month=12, day=31)
    elif len(s) == 7:
        format = '%Y-%m'
        result = datetime.datetime.strptime(s, format)
        if round == 'up':
            if result.month == 12:
                result = result.replace(month=1, year=result.year + 1)
                result = result - datetime.timedelta(1)
            else: 
                result = result.replace(month=result.month+1)
                result = result - datetime.timedelta(1)
    elif len(s) == 10:
        format = '%Y-%m-%d'
        result = datetime.datetime.strptime(s, format)
    else:
        raise ValueError('This data is not in ISO date format:%s' % s)
        
    return result

def format_date(d):
    """take a datetime instance, return a string
    
    (use this because strftime does not like dates before 1900)"""
    if d:
        return u"%04d-%02d-%02d %02d:%02d" % (d.year,d.month,d.day,d.hour,d.minute)
    
    