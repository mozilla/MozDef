from datetime import datetime
from dateutil.parser import parse
import pytz

def toUTC(suspectedDate, localTimeZone='UTC'):
    '''make a UTC date out of almost anything'''

    utc=pytz.UTC
    objDate=None

    if type(suspectedDate) == datetime:
        objDate = suspectedDate
    elif str(suspectedDate).isdigit():
        # epoch? but seconds/milliseconds/nanoseconds (lookin at you heka)
        epochDivisor = int(str(1) + '0'*(len(str(suspectedDate)) % 10))
        objDate = datetime.fromtimestamp(float(suspectedDate/epochDivisor))
    elif type(suspectedDate) in (str, unicode):
        objDate = parse(suspectedDate, fuzzy=True)

    if objDate.tzinfo is None:
        objDate=pytz.timezone(localTimeZone).localize(objDate)

    objDate=utc.normalize(objDate)

    return objDate
