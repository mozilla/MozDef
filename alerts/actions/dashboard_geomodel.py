# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation

import hjson
import os
from binascii import b2a_hex
import boto3
import datetime
import json
from ipwhois import IPWhois

from mozdef_util.utilities.logger import logger
from mozdef_util.utilities.toUTC import toUTC


class message(object):
    def __init__(self):
        '''
        sends geomodel alert to SSO dashboard
        '''
        self.alert_classname = 'AlertGeomodel'

        config_file_path = os.path.join(os.path.dirname(__file__), 'dashboard_geomodel.json')
        json_obj = {}
        with open(config_file_path, "r") as fd:
            try:
                json_obj = hjson.load(fd)
            except ValueError:
                logger.error("FAILED to open the configuration file" + str(config_file_path))
        self.config = json_obj

        self.connect_db()

        self.registration = 'geomodel'
        self.priority = 1

    def connect_db(self):
        boto_session = boto3.session.Session(
            aws_access_key_id=self.config['aws_access_key_id'],
            aws_secret_access_key=self.config['aws_secret_access_key'],
            region_name=self.config['aws_region']
        )

        dynamodb_resource = boto_session.resource('dynamodb')
        table = dynamodb_resource.Table(self.config['db_table'])
        self.dynamodb = table

    def write_db_entry(self, alert_record):
        self.dynamodb.put_item(Item=alert_record)

    def onMessage(self, alert):
        # As of Dec. 3, 2019, alert actions are given entire alerts rather
        # than just their source
        message = alert['_source']

        if 'details' not in message:
            return message

        if 'principal' not in message['details']:
            return message

        if 'category' not in message['details']:
            return message

        if message['details']['category'].lower() != 'newcountry':
            return message

        full_email = message['details']['principal']
        username = full_email.split('@')[0]
        auth_full_username = self.config['auth_id_prefix'] + username

        if 'city' not in message['details']['locality_details']:
            return message

        if 'country' not in message['details']['locality_details']:
            return message

        if 'source_ip' not in message['details']:
            return message

        city = message['details']['locality_details']['city']
        country = message['details']['locality_details']['country']
        source_ip = message['details']['source_ip']

        new_ip_info = ""
        try:
            whois = IPWhois(source_ip).lookup_whois()
            whois_str = whois['nets'][0]['description']
            source_ip_isp = whois_str.replace('\n', ', ').replace('\r', '')
            new_ip_info = '{} ({})'.format(source_ip, source_ip_isp)
        except Exception:
            new_ip_info = '{}'.format(source_ip)

        new_location_str = ""
        if city.lower() == 'unknown':
            new_location_str += '{0}'.format(country)
        else:
            new_location_str += '{0}, {1}'.format(city, country)

        event_timestamp = toUTC(message['events'][0]['documentsource']['details']['event_time'])
        event_day = event_timestamp.strftime('%B %d, %Y')
        summary = 'On {0} (UTC), did you login from {1} ({2})?'.format(event_day, new_location_str, source_ip)

        previous_city = message['details']['previous_locality_details']['city']
        previous_country = message['details']['previous_locality_details']['country']
        if previous_city.lower() == 'unknown':
            previous_location_str = '{0}'.format(previous_country)
        else:
            previous_location_str = '{0}, {1}'.format(previous_city, previous_country)

        alert_record = {
            'alert_id': b2a_hex(os.urandom(15)).decode(),
            'alert_code': b2a_hex(self.alert_classname.encode()).decode(),
            'user_id': auth_full_username,
            'risk': self.config['risk'],
            'summary': summary,
            'description': self.config['description'],
            'date': str(datetime.date.today()),
            'url': self.config['url'],
            'url_title': self.config['url_title'],
            'duplicate': self.config['duplicate'],
            'alert_str_json': json.dumps(message),
            'details': {
                'Timestamp': event_timestamp.strftime('%A, %B %d %Y %H:%M UTC'),
                'New Location': new_location_str,
                'New IP': new_ip_info,
                'Previous Location': previous_location_str
            }
        }
        self.write_db_entry(alert_record)
        return message
