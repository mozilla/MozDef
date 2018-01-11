def toUnicode(obj, encoding='utf-8'):
    if type(obj) in [int, long, float, complex]:
        # likely a number, convert it to string to get to unicode
        obj = str(obj)
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj
