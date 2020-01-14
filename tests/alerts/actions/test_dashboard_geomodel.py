import json

from alerts.actions.dashboard_geomodel import message


class TestDashboardGeomodel(object):

    def mock_write_db_entry(self, alert_record):
        self.test_result_record = alert_record

    def mock_connect_db(self):
        self.test_connect_called = True

    def setup(self):
        # Mock boto service required methods
        message.connect_db = self.mock_connect_db
        message.write_db_entry = self.mock_write_db_entry
        self.test_result_record = None
        self.test_connect_called = False

        self.plugin = message()
        self.good_message_dict = {
            "_source": {
                "category": "geomodel",
                "tags": ['geomodel'],
                "summary": "ttesterson@mozilla.com NEWCOUNTRY Diamond Bar, United States access from 1.2.3.4 (duo) [deviation:12.07010770457331] last activity was from Ottawa, Canada (3763 km away) approx 23.43 hours before",
                "events": [
                    {
                        'documentsource': {
                            'details': {
                                'event_time': '2018-08-08T02:11:41.85Z',
                            }
                        }
                    }
                ],
                "details": {
                    "category": "NEWCOUNTRY",
                    'previous_locality_details': {
                        'city': 'Oakland',
                        'country': 'United States'
                    },
                    "locality_details": {
                        "city": "Diamond Bar",
                        "country": "United States"
                    },
                    'source_ip': '1.2.3.4',
                    "principal": "ttesterson@mozilla.com",
                }
            }
        }

    def test_message_good(self):
        assert self.test_result_record is None
        result_message = self.plugin.onMessage(self.good_message_dict)
        assert result_message == self.good_message_dict['_source']
        assert self.test_connect_called is True
        result_db_entry = self.test_result_record
        assert type(result_db_entry['alert_code']) is str
        assert len(result_db_entry['alert_code']) == 26
        assert type(result_db_entry['alert_id']) is str
        assert len(result_db_entry['alert_id']) == 30
        assert result_db_entry['alert_code'] != result_db_entry['alert_id']
        assert type(result_db_entry['date']) == str
        assert result_db_entry['description'] == 'This alert is created based on geo ip information about the last login of a user.'
        assert result_db_entry['duplicate'] is True
        assert result_db_entry['risk'] == 'high'
        assert result_db_entry['summary'] == 'On August 08, 2018 (UTC), did you login from Diamond Bar, United States (1.2.3.4)?'
        assert result_db_entry['url'] == 'https://www.mozilla.org'
        assert result_db_entry['url_title'] == 'Get Help'
        assert result_db_entry['user_id'] == 'ttesterson'
        assert result_db_entry['alert_str_json'] == json.dumps(self.good_message_dict['_source'])

    def test_unknown_new_city_message(self):
        message_dict = self.good_message_dict
        message_dict['_source']['details']['locality_details']['city'] = 'UNKNOWN'
        assert self.test_result_record is None
        result_message = self.plugin.onMessage(message_dict)
        assert result_message == self.good_message_dict['_source']
        assert self.test_connect_called is True
        result_db_entry = self.test_result_record
        assert type(result_db_entry['alert_code']) is str
        assert result_db_entry['summary'] == 'On August 08, 2018 (UTC), did you login from United States (1.2.3.4)?'

    def test_malformed_message_bad(self):
        message_dict = {
            "_source": {
                "category": "geomodel",
                "tags": ['geomodel'],
                "summary": "ttesterson@mozilla.com MOVEMENT Diamond Bar, United States access from 1.2.3.4 (duo) [deviation:12.07010770457331] last activity was from Ottawa, Canada (3763 km away) approx 23.43 hours before",
                "details": {
                    "category": "MOVEMENT",
                    "locality_details": {
                        "city": "Diamond Bar",
                        "country": "United States"
                    },
                    "principal": "ttesterson@mozilla.com",
                }
            }
        }

        assert self.test_result_record is None
        result_message = self.plugin.onMessage(message_dict)
        assert result_message == message_dict['_source']
        assert self.test_connect_called is True
        assert self.test_result_record is None

    def test_str_location(self):
        self.good_message_dict['_source']['summary'] = "ttesterson@mozilla.com NEWCOUNTRY \u0107abcd, \xe4Spain access from 1.2.3.4 (duo) [deviation:12.07010770457331] last activity was from Ottawa, Canada (3763 km away) approx 23.43 hours before"
        self.good_message_dict['_source']['details']['locality_details']['city'] = '\u0107abcd'
        self.good_message_dict['_source']['details']['locality_details']['country'] = '\xe4Spain'
        assert self.test_result_record is None
        result_message = self.plugin.onMessage(self.good_message_dict)
        assert result_message == self.good_message_dict['_source']
        assert self.test_connect_called is True
        assert self.test_result_record is not None
        assert type(result_message['summary']) is str
        assert type(result_message['details']['locality_details']['city']) is str
        assert type(result_message['details']['locality_details']['country']) is str

    def test_str_username(self):
        self.good_message_dict['_source']['details']['principal'] = '\xfcttesterson@mozilla.com'
        assert self.test_result_record is None
        result_message = self.plugin.onMessage(self.good_message_dict)
        assert result_message == self.good_message_dict['_source']
        assert self.test_connect_called is True
        assert self.test_result_record is not None
        assert type(result_message['summary']) is str
        assert type(result_message['details']['principal']) is str

    def test_written_details(self):
        assert self.test_result_record is None
        result_message = self.plugin.onMessage(self.good_message_dict)
        assert result_message == self.good_message_dict['_source']
        assert self.test_connect_called is True
        assert self.test_result_record is not None
        result_db_entry = self.test_result_record
        assert result_db_entry['details'] == {
            'New IP': '1.2.3.4 (APNIC Debogon Project, APNIC Pty Ltd)',
            'New Location': 'Diamond Bar, United States',
            'Previous Location': 'Oakland, United States',
            'Timestamp': 'Wednesday, August 08 2018 02:11 UTC'
        }
