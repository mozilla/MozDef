import json


class StateParsingError(ValueError):
    pass


class State:
    def __init__(self, filename):
        '''Set the filename and populate self.data by calling self.read_stat_file()'''
        self.filename = filename
        self.read()

    def read(self):
        '''Populate self.data by reading and parsing the state file'''
        try:
            with open(self.filename, 'r') as f:
                self.data = json.load(f)
        except IOError:
            self.data = {}
        except ValueError:
            raise StateParsingError(
                "%s state file found but isn't a recognized json format" % self.filename)

    def save(self):
        '''Write the self.data value into the state file'''
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, sort_keys=True, indent=4, separators=(',', ': '))
