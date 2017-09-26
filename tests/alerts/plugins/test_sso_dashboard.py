import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../alerts/plugins"))
from sso_dashboard import message


class TestSSODashboard(object):

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

    def test_geoip_message(self):
        message_dict = {
            "category": "geomodel",
            "tags": [
                "geomodel"
            ],
            "summary": "ttesterson@mozillafoundation.org NEWCOUNTRY Saint-Jean-sur-Richelieu, Canada access from 1.2.3.4 (duo) [deviation:2] last activity was from Stuarts Draft, United States (941 km away) approx 97.49 hours before",
        }

        assert self.test_result_record is None
        result_message = self.plugin.onMessage(message_dict)
        assert result_message == message_dict
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
        assert result_db_entry['summary'] == 'Did you recently login from Saint-Jean-sur-Richelieu, Canada?'
        assert result_db_entry['url'] == 'https://www.mozilla.org'
        assert result_db_entry['url_title'] == 'Get Help'
        assert result_db_entry['user_id'] == 'ttesterson'
