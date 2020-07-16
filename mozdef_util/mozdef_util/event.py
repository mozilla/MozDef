from datetime import datetime
import socket

from .utilities.toUTC import toUTC


class Event(dict):

    # We set default vaules so that we can later
    # create an alert around these, and know when events
    # have to use defaults
    DEFAULT_STRING = 'UNKNOWN'
    DEFAULT_TYPE = 'event'

    def add_required_fields(self):
        if 'receivedtimestamp' not in self:
            self['receivedtimestamp'] = toUTC(datetime.now()).isoformat()
        if 'utctimestamp' not in self:
            self['utctimestamp'] = toUTC(datetime.now()).isoformat()
        if 'timestamp' not in self:
            self['timestamp'] = toUTC(datetime.now()).isoformat()
        if 'mozdefhostname' not in self:
            self['mozdefhostname'] = socket.gethostname()
        if 'type' not in self:
            self['type'] = self.DEFAULT_TYPE
        if 'tags' not in self:
            self['tags'] = []
        if 'category' not in self:
            self['category'] = self.DEFAULT_STRING
        if 'hostname' not in self:
            self['hostname'] = self.DEFAULT_STRING
        if 'processid' not in self:
            self['processid'] = self.DEFAULT_STRING
        if 'processname' not in self:
            self['processname'] = self.DEFAULT_STRING
        if 'severity' not in self:
            self['severity'] = self.DEFAULT_STRING
        if 'source' not in self:
            self['source'] = self.DEFAULT_STRING
        if 'summary' not in self:
            self['summary'] = self.DEFAULT_STRING
        if 'mozdef' not in self:
            self['mozdef'] = {}
        if 'plugins' not in self['mozdef']:
            self['mozdef']['plugins'] = []
        if 'details' not in self:
            self['details'] = {}
