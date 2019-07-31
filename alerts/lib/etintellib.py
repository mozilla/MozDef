#!/usr/bin/env python
import pprint
from configlib import getConfig, OptionParser
from datetime import datetime, timedelta
import json
import requests
import netaddr
import sys

intel = ''

class etintel():

    def __init__(self, intel, options):
        self.reputation = {}
        self.intel = intel
        self.options = options


    def sendRequest(self, reqtype):
        headers = {'Authorization': self.options.apikey}
        url = ''
        self.rawdata = dict()
        if netaddr.valid_ipv4(self.intel):
            url = "https://" + self.options.apiurl + "/ips/" + self.intel + "/" + reqtype
        else:
            url = "https://" + self.options.apiurl + "/domains/" + self.intel + "/" + reqtype
        if len(reqtype) and len(url) > 1:
            try:
                request = requests.get(url=url, headers=headers, timeout=2)
                print(request)
            except (
                    requests.exceptions.ConnectionError, requests.exceptions.TooManyRedirects,
                    requests.exceptions.Timeout) as e:
                sys.stderr.write('Failed to fetch IQRisk data: {0}\n'.format(e))
            if 'request' in locals() and hasattr(request, 'json'):
                if request.status_code == 200:
                    try:
                        self.rawdata = request.json()
                    except (ValueError) as e:
                        sys.stderr.write('Failed to decode IQRisk data: {0}\n'.format(e))

    def get_reputation(self, type, objtype):
        self.reputation[type] = dict()
        if objtype == 'ip':
            if type in self.options.allowedipreptypes:
                self.sendRequest(type)
        if objtype == 'domain':
            self.sendRequest(type)
        if 'response' in self.rawdata:
            if self.rawdata['response'] and self.rawdata['success']:
                self.reputation[type] = self.rawdata['response']
