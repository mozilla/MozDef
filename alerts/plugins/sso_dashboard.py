# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Brandon Myers bmyers@mozilla.com

import hjson
import os
import sys
from binascii import b2a_hex
import boto3
import datetime

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../lib'))
from utilities.logger import logger


class message(object):
    def __init__(self):
        '''
        sends certain messages to an SSO dashboard
        '''
        # Configuration loading
        config_file_path = os.path.join(os.path.dirname(__file__), 'sso_dashboard.json')
        json_obj = {}
        with open(config_file_path, "r") as fd:
            try:
                json_obj = hjson.load(fd)
            except ValueError:
                logger.error("FAILED to open the configuration file" + str(config_file_path))
        self.config = json_obj

        # Set the alert ids based on alert name
        for name, alert in self.config['alerts'].iteritems():
            alert['alert_code'] = b2a_hex(name)

        self.connect_db()

        self.registration = '*'
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

    def onMessage(self, message):
        for name, alert in self.config['alerts'].iteritems():
            # we have a message that matches an alert we care about
            if message['category'] == alert['category']:
                full_email = message['details']['principal']
                username = full_email.split('@')[0]
                auth_full_username = self.config['auth_id_prefix'] + username
                city = message['details']['locality_details']['city']
                country = message['details']['locality_details']['country']
                summary = alert['summary'].format(city, country)

                alert_record = {
                    'alert_id': b2a_hex(os.urandom(15)),
                    'alert_code': alert['alert_code'],
                    'user_id': auth_full_username,
                    'risk': alert['risk'],
                    'summary': summary,
                    'description': alert['description'],
                    'date': str(datetime.date.today()),
                    'url': alert['url'],
                    'url_title': alert['url_title'],
                    'duplicate': alert['duplicate'],
                }
                self.write_db_entry(alert_record)

        return message
