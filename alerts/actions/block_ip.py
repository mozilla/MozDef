import requests
import json
import os
from configlib import getConfig, OptionParser
from requests_jwt import JWTAuth


class message(object):
    def __init__(self):
        '''
        takes an incoming alert
        and triggers the block ip rest api endpoint
        '''

        self.configfile = os.path.join(os.path.dirname(__file__), 'block_ip.conf')
        self.options = None
        if os.path.exists(self.configfile):
            self.initConfiguration()
        if self.options.restapi_jwt_token is not None:
            self._restapi_jwt = JWTAuth(self.options.restapi_jwt_token)
            self._restapi_jwt.set_header_format('Bearer %s')
        else:
            self._restapi_jwt = None

        self.registration = self.options.alert_names.split(" ")
        # Block for 1 day
        self.DEFAULT_BLOCK_LENGTH = "1d"
        self.priority = 1

    def initConfiguration(self):
        myparser = OptionParser()
        (self.options, args) = myparser.parse_args([])

        self.options.alert_names = getConfig('alert_names', [], self.configfile)
        self.options.restapi_url = getConfig('restapi_url', '', self.configfile)
        self.options.restapi_jwt_token = getConfig('restapi_jwt_token', None, self.configfile)

    def onMessage(self, alert):
        message = alert['_source']
        post_data = [
            {'ipaddress': "{0}/32".format(message['details']['sourceipaddress'])},
            {'duration': self.DEFAULT_BLOCK_LENGTH},
            {'comment': 'Automatic Block'},
            {'referenceid': ''},
            {'IPBlockList': True},
            {'userid': "MozDef"}
        ]
        headers = {'Content-type': 'application/json'}
        resp = requests.post(url=self.options.restapi_url + "/blockip", data=json.dumps(post_data), auth=self._restapi_jwt, headers=headers)
        if not resp.ok:
            raise Exception("Received error {0} from rest api when updating alerts schedules {1}".format(resp.status_code, resp.data))
        return message
