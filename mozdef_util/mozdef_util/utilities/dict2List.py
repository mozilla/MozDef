from datetime import datetime


def dict2List(value):
    '''Convert dictionaries into a list of keys and values,
    with strings in lowercase and datetimes converted to isoformat.
    '''

    if isinstance(value, dict):
        for key, val in value.items():
            yield from dict2List(key)
            yield from dict2List(val)
    elif isinstance(value, (list, tuple)):
        for val in value:
            yield from dict2List(val)
    elif isinstance(value, datetime):
        yield value.isoformat()
    elif isinstance(value, str):
        yield value.lower()
    else:
        yield value
