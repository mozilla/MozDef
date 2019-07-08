def dict2List(inObj):
    '''given a dictionary, potentially with multiple sub dictionaries
       return a list of the dict keys and values
    '''
    if isinstance(inObj, dict):
        for key, value in inObj.items():
            if isinstance(value, dict):
                for d in dict2List(value):
                    yield d
            elif isinstance(value, list):
                yield key.lower()
                for l in dict2List(value):
                    yield l
            else:
                yield key.lower()
                if isinstance(value, str):
                    yield value.lower()
                else:
                    yield value
    elif isinstance(inObj, list):
        for v in inObj:
            if isinstance(v, str):
                yield v.lower()
            elif isinstance(v, list):
                for l in dict2List(v):
                    yield l
            elif isinstance(v, dict):
                for l in dict2List(v):
                    yield l
            else:
                yield v
    else:
        yield ''
