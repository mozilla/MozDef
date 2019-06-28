def toUnicode(obj, encoding='utf-8'):
    if not isinstance(obj, str):
        obj = str(obj, encoding)
    return obj
