from datetime import datetime
from dateutil.parser import parse
import pytz

def toUTC(suspectedDate, localTimeZone='UTC'):
    '''make a UTC date out of almost anything'''

    utc=pytz.UTC
    objDate=None

    if type(suspectedDate) in (str,unicode):
        objDate=parse(suspectedDate,fuzzy=True)
    elif type(suspectedDate)==datetime:
        objDate=suspectedDate

    if objDate.tzinfo is None:
        objDate=pytz.timezone(localTimeZone).localize(objDate)
        objDate=utc.normalize(objDate)
    else:
        objDate=utc.normalize(objDate)

    if objDate is not None:
        objDate=utc.normalize(objDate)

    return objDate
