def isCEF(aDict):
    # determine if this is a CEF event
    # could be an event posted to the /cef http endpoint
    if 'endpoint' in aDict and aDict['endpoint'] == 'cef':
        return True
    # maybe it snuck in some other way
    # check some key CEF indicators (the header fields)
    if 'fields' in aDict and isinstance(aDict['fields'], dict):
        lowerKeys = [s.lower() for s in aDict['fields'].keys()]
        if 'devicevendor' in lowerKeys and 'deviceproduct' in lowerKeys and 'deviceversion' in lowerKeys:
            return True
    if 'details' in aDict and isinstance(aDict['details'], dict):
        lowerKeys = [s.lower() for s in aDict['details'].keys()]
        if 'devicevendor' in lowerKeys and 'deviceproduct' in lowerKeys and 'deviceversion' in lowerKeys:
            return True
    return False
