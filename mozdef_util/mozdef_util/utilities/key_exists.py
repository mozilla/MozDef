
def key_exists(search_key, inputed_dict):
    '''
    Given a search key which is dot notated
    return wether or not that key exists in a dictionary
    '''
    num_levels = search_key.split(".")
    if len(num_levels) == 0:
        return False
    current_pointer = inputed_dict
    for updated_key in num_levels:
        if current_pointer is None:
            return False
        if updated_key == num_levels[-1]:
            return updated_key in current_pointer
        if updated_key in current_pointer:
            current_pointer = current_pointer[updated_key]
        else:
            return False
