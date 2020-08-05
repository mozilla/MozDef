#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://website.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

import datetime

from mozdef_util.utilities.dict2List import dict2List

from tests.unit_test_suite import UnitTestSuite


TEST_ALERT = {
    "utctimestamp": "2020-04-23T22:54:53.708859+00:00",
    "severity": "WARNING",
    "summary": "tester@website.com seen in Anaheim,US then San Diego,US (124.23 KM in 0.01 minutes); San Diego,US then Anaheim,US (124.23 KM in 4.41 minutes); Anaheim,US then San Diego,US (124.23 KM in 0.01 minutes); Anaheim,US then San Diego,US (124.23 KM in 0.01 minutes)",
    "category": "geomodel",
    "tags": ["geomodel"],
    "events": [
        {
            "documentindex": "events-20200422",
            "documentsource": {
                "receivedtimestamp": "2020-04-22T21:31:35.274785+00:00",
                "mozdefhostname": "mozdef.website.com",
                "details": {
                    "access_device": {
                        "hostname": None,
                        "ip": "1.2.3.4",
                        "location": {
                            "city": "Fontana",
                            "country": "United States",
                            "state": "California",
                        },
                    },
                    "alias": "",
                    "application": {
                        "key": "DI1MFG5M5N5GZIEBVCY2",
                        "name": "Mozilla Auth0 Prod",
                    },
                    "auth_device": {
                        "ip": "1.2.3.4",
                        "location": {
                            "city": "Fontana",
                            "country": "United States",
                            "state": "California",
                        },
                        "name": "858-472-2244",
                    },
                    "email": "",
                    "event_type": "authentication",
                    "factor": "duo_push",
                    "isotimestamp": "2020-04-22T15:05:27.410180+00:00",
                    "reason": "user_approved",
                    "result": "success",
                    "sourceipaddress": "1.2.3.4",
                    "success": True,
                    "txid": "ce2e7158-f1a3-4b34-8488-3ccaf39ca30d",
                    "userkey": "DU3WROU2UXE8NA7138EL",
                    "username": "tester@website.com",
                    "sourceipv4address": "1.2.3.4",
                    "sourceipgeolocation": {
                        "city": "Anaheim",
                        "continent": "NA",
                        "country_code": "US",
                        "country_name": "United States",
                        "dma_code": 803,
                        "latitude": 33.8405,
                        "longitude": -117.9526,
                        "metro_code": "Anaheim, CA",
                        "postal_code": "92801",
                        "region_code": "CA",
                        "time_zone": "America/Los_Angeles",
                    },
                    "sourceipgeopoint": "33.8405,-117.9526",
                },
                "category": "authentication",
                "hostname": "mozdef.website.com",
                "processid": "10391",
                "processname": "/opt/mozdef/envs/mozdef/cron/duo_logpull.py",
                "severity": "INFO",
                "summary": "authentication success for tester@website.com",
                "tags": ["duosecurity"],
                "utctimestamp": "2020-04-22T21:31:35.274785+00:00",
                "timestamp": "2020-04-22T21:31:35.274785+00:00",
                "type": "event",
                "mozdef": {
                    "plugins": [
                        "ipFixup", "geoip"
                    ]
                },
                "source": "UNKNOWN",
            },
            "documentid": "JN7No3EBh9xp2NOIpD4Q",
        },
        {
            "documentindex": "events-20200422",
            "documentsource": {
                "receivedtimestamp": "2020-04-22T21:31:35.564107+00:00",
                "mozdefhostname": "mozdef.website.com",
                "details": {
                    "clientid": "TnqNECyCfoQYd1X7c4xwMF4PMsEfyWPj",
                    "clientname": "website.zoom.us",
                    "connection": "Mozilla-LDAP",
                    "description": "None",
                    "eventname": "Success Login",
                    "messageid": "5ea05d38d28ace0714820128",
                    "raw": "{'_id': '5ea05d38d28ace0714820128', 'date': '2020-04-22T15:05:28.374Z', 'type': 's', 'description': 'None', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'client_id': 'TnqNECyCfoQYd1X7c4xwMF4PMsEfyWPj', 'client_name': 'website.zoom.us', 'ip': '1.2.3.4', 'client_ip': 'None', 'user_agent': 'Firefox Mobile 75.0.0 / Android 0.0.0', 'details': {'prompts': [{'name': 'lock-password-authenticate', 'initiatedAt': '1587567915617', 'completedAt': '1587567915964', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'strategy': 'ad', 'identity': 'Mozilla-LDAP|tester', 'stats': {'loginsCount': '2314'}, 'session_user': '5ea05d2b5441aa04697bbe2e', 'elapsedTime': '347'}, {'name': 'login', 'flow': 'login', 'initiatedAt': '1587567905584', 'completedAt': '1587567915965', 'timers': {'rules': '386'}, 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'elapsedTime': '10381'}, {'name': 'mfa', 'flow': 'mfa', 'initiatedAt': '1587567916358', 'completedAt': '1587567928352', 'performed_acr': ['http://schemas.openid.net/pape/policies/2007/06/multi-factor'], 'performed_amr': ['mfa'], 'provider': 'duo', 'elapsedTime': '11994'}], 'initiatedAt': '1587567905582', 'completedAt': '1587567928372', 'elapsedTime': '22790', 'session_id': 'xUneHabcm83WvtggcG-csaKqfjUCY9Uw', 'device_id': 'v0:88c38ae0-343c-11ea-888a-8fb9710d9719', 'stats': {'loginsCount': '2314'}}, 'hostname': 'auth.website.auth0.com', 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'strategy': 'ad', 'strategy_type': 'enterprise', 'isMobile': 'True'}",
                    "sourceipaddress": "1.2.3.4",
                    "success": True,
                    "useragent": "Firefox Mobile 75.0.0 / Android 0.0.0",
                    "userid": "ad|Mozilla-LDAP|tester",
                    "username": "tester@website.com",
                    "sourceipv4address": "1.2.3.4",
                    "sourceipgeolocation": {
                        "city": "Anaheim",
                        "continent": "NA",
                        "country_code": "US",
                        "country_name": "United States",
                        "dma_code": 803,
                        "latitude": 33.8405,
                        "longitude": -117.9526,
                        "metro_code": "Anaheim, CA",
                        "postal_code": "92801",
                        "region_code": "CA",
                        "time_zone": "America/Los_Angeles",
                    },
                    "sourceipgeopoint": "33.8405,-117.9526",
                },
                "category": "authentication",
                "hostname": "https://auth.website.auth0.com/api/v2/logs",
                "processid": "9101",
                "processname": "/opt/mozdef/envs/mozdef/cron/auth02mozdef.py",
                "severity": "INFO",
                "summary": "Success Login tester@website.com",
                "tags": ["auth0"],
                "utctimestamp": "2020-04-22T21:31:35.564107+00:00",
                "timestamp": "2020-04-22T21:31:35.564107+00:00",
                "type": "event",
                "mozdef": {
                    "plugins": [
                        "ipFixup", "geoip"
                    ]
                },
                "source": "UNKNOWN",
            },
            "documentid": "Jd7No3EBh9xp2NOIpT40",
        },
        {
            "documentindex": "events-20200422",
            "documentsource": {
                "receivedtimestamp": "2020-04-22T21:31:35.852684+00:00",
                "mozdefhostname": "mozdef.website.com",
                "details": {
                    "clientid": "Qzs1IbNmnXB1js1KlhhdnwYZT9rwwF4U",
                    "clientname": "mana.website.org - new",
                    "connection": "Mozilla-LDAP",
                    "description": "None",
                    "eventname": "Success Login",
                    "messageid": "5ea05d825ae00a0d5de5d174",
                    "raw": "{'_id': '5ea05d825ae00a0d5de5d174', 'date': '2020-04-22T15:06:42.179Z', 'type': 's', 'description': 'None', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'client_id': 'Qzs1IbNmnXB1js1KlhhdnwYZT9rwwF4U', 'client_name': 'mana.website.org - new', 'ip': '1.2.3.4', 'client_ip': 'None', 'user_agent': 'Firefox Mobile 75.0.0 / Android 0.0.0', 'details': {'prompts': [{'name': 'authenticate', 'initiatedAt': '1587568001564', 'completedAt': '1587568001742', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'strategy': 'ad', 'identity': 'Mozilla-LDAP|tester', 'stats': {'loginsCount': '2315'}, 'elapsedTime': '178'}, {'name': 'login', 'flow': 'login', 'initiatedAt': '1587567997696', 'completedAt': '1587568001746', 'timers': {'rules': '419'}, 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'elapsedTime': '4050'}], 'initiatedAt': '1587567997694', 'completedAt': '1587568002178', 'elapsedTime': '4484', 'session_id': 'xUneHabcm83WvtggcG-csaKqfjUCY9Uw', 'device_id': 'v0:88c38ae0-343c-11ea-888a-8fb9710d9719', 'stats': {'loginsCount': '2315'}}, 'hostname': 'auth.website.auth0.com', 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'strategy': 'ad', 'strategy_type': 'enterprise', 'isMobile': 'True'}",
                    "sourceipaddress": "1.2.3.4",
                    "success": True,
                    "useragent": "Firefox Mobile 75.0.0 / Android 0.0.0",
                    "userid": "ad|Mozilla-LDAP|tester",
                    "username": "tester@website.com",
                    "sourceipv4address": "1.2.3.4",
                    "sourceipgeolocation": {
                        "city": "Anaheim",
                        "continent": "NA",
                        "country_code": "US",
                        "country_name": "United States",
                        "dma_code": 803,
                        "latitude": 33.8405,
                        "longitude": -117.9526,
                        "metro_code": "Anaheim, CA",
                        "postal_code": "92801",
                        "region_code": "CA",
                        "time_zone": "America/Los_Angeles",
                    },
                    "sourceipgeopoint": "33.8405,-117.9526",
                },
                "category": "authentication",
                "hostname": "https://auth.website.auth0.com/api/v2/logs",
                "processid": "9431",
                "processname": "/opt/mozdef/envs/mozdef/cron/auth02mozdef.py",
                "severity": "INFO",
                "summary": "Success Login tester@website.com",
                "tags": ["auth0"],
                "utctimestamp": "2020-04-22T21:31:35.852684+00:00",
                "timestamp": "2020-04-22T21:31:35.852684+00:00",
                "type": "event",
                "mozdef": {
                    "plugins": [
                        "ipFixup", "geoip"
                    ]
                },
                "source": "UNKNOWN",
            },
            "documentid": "Jt7No3EBh9xp2NOIpj5T",
        },
        {
            "documentindex": "events-20200422",
            "documentsource": {
                "receivedtimestamp": "2020-04-22T21:31:36.427461+00:00",
                "mozdefhostname": "mozdef.website.com",
                "details": {
                    "clientid": "smKTjsVVxUJDEkjIftOsP0bop2NWjysa",
                    "clientname": "Google (website.com)",
                    "connection": "Mozilla-LDAP",
                    "description": "None",
                    "eventname": "Success Login",
                    "messageid": "5ea068294ecfef0d5ede734f",
                    "raw": "{'_id': '5ea068294ecfef0d5ede734f', 'date': '2020-04-22T15:52:09.136Z', 'type': 's', 'description': 'None', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'client_id': 'smKTjsVVxUJDEkjIftOsP0bop2NWjysa', 'client_name': 'Google (website.com)', 'ip': '1.2.3.4', 'client_ip': 'None', 'user_agent': 'Firefox 75.0.0 / Mac OS X 10.14.0', 'details': {'prompts': [{'name': 'authenticate', 'initiatedAt': '1587570728596', 'completedAt': '1587570728676', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'strategy': 'ad', 'identity': 'Mozilla-LDAP|tester', 'stats': {'loginsCount': '2317'}, 'elapsedTime': '80'}, {'name': 'login', 'flow': 'login', 'initiatedAt': '1587570728072', 'completedAt': '1587570728680', 'timers': {'rules': '444'}, 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'elapsedTime': '608'}], 'initiatedAt': '1587570728071', 'completedAt': '1587570729135', 'elapsedTime': '1064', 'session_id': 'iHzeCh-tAqtAj_onA-Xm1jO-w45jsng8', 'device_id': 'v0:01b67bb0-17b4-11ea-8202-9fb43e6ec9e0', 'stats': {'loginsCount': '2317'}}, 'hostname': 'auth.website.auth0.com', 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'strategy': 'ad', 'strategy_type': 'enterprise', 'isMobile': 'False'}",
                    "sourceipaddress": "4.3.2.1",
                    "success": True,
                    "useragent": "Firefox 75.0.0 / Mac OS X 10.14.0",
                    "userid": "ad|Mozilla-LDAP|tester",
                    "username": "tester@website.com",
                    "sourceipv4address": "4.3.2.1",
                    "sourceipgeolocation": {
                        "city": "San Diego",
                        "continent": "NA",
                        "country_code": "US",
                        "country_name": "United States",
                        "dma_code": 825,
                        "latitude": 32.9661,
                        "longitude": -117.1202,
                        "metro_code": "San Diego, CA",
                        "postal_code": "92129",
                        "region_code": "CA",
                        "time_zone": "America/Los_Angeles",
                    },
                    "sourceipgeopoint": "32.9661,-117.1202",
                },
                "category": "authentication",
                "hostname": "https://auth.website.auth0.com/api/v2/logs",
                "processid": "21204",
                "processname": "/opt/mozdef/envs/mozdef/cron/auth02mozdef.py",
                "severity": "INFO",
                "summary": "Success Login tester@website.com",
                "tags": ["auth0"],
                "utctimestamp": "2020-04-22T21:31:36.427461+00:00",
                "timestamp": "2020-04-22T21:31:36.427461+00:00",
                "type": "event",
                "mozdef": {
                    "plugins": [
                        "ipFixup", "geoip"
                    ]
                },
                "source": "UNKNOWN",
            },
            "documentid": "KN7No3EBh9xp2NOIqD6R",
        },
        {
            "documentindex": "events-20200422",
            "documentsource": {
                "receivedtimestamp": "2020-04-22T21:31:36.713494+00:00",
                "mozdefhostname": "mozdef.website.com",
                "details": {
                    "clientid": "smKTjsVVxUJDEkjIftOsP0bop2NWjysa",
                    "clientname": "Google (website.com)",
                    "connection": "Mozilla-LDAP",
                    "description": "None",
                    "eventname": "Success Login",
                    "messageid": "5ea068a9f995810715819b3e",
                    "raw": "{'_id': '5ea068a9f995810715819b3e', 'date': '2020-04-22T15:54:17.352Z', 'type': 's', 'description': 'None', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'client_id': 'smKTjsVVxUJDEkjIftOsP0bop2NWjysa', 'client_name': 'Google (website.com)', 'ip': '4.3.2.1', 'client_ip': 'None', 'user_agent': 'Firefox 75.0.0 / Mac OS X 10.14.0', 'details': {'prompts': [{'name': 'authenticate', 'initiatedAt': '1587570856858', 'completedAt': '1587570856931', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'strategy': 'ad', 'identity': 'Mozilla-LDAP|tester', 'stats': {'loginsCount': '2318'}, 'elapsedTime': '73'}, {'name': 'login', 'flow': 'login', 'initiatedAt': '1587570856299', 'completedAt': '1587570856933', 'timers': {'rules': '407'}, 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'elapsedTime': '634'}], 'initiatedAt': '1587570856298', 'completedAt': '1587570857351', 'elapsedTime': '1053', 'session_id': 'iHzeCh-tAqtAj_onA-Xm1jO-w45jsng8', 'device_id': 'v0:01b67bb0-17b4-11ea-8202-9fb43e6ec9e0', 'stats': {'loginsCount': '2318'}}, 'hostname': 'auth.website.auth0.com', 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'strategy': 'ad', 'strategy_type': 'enterprise', 'isMobile': 'False'}",
                    "sourceipaddress": "4.3.2.1",
                    "success": True,
                    "useragent": "Firefox 75.0.0 / Mac OS X 10.14.0",
                    "userid": "ad|Mozilla-LDAP|tester",
                    "username": "tester@website.com",
                    "sourceipv4address": "4.3.2.1",
                    "sourceipgeolocation": {
                        "city": "San Diego",
                        "continent": "NA",
                        "country_code": "US",
                        "country_name": "United States",
                        "dma_code": 825,
                        "latitude": 32.9661,
                        "longitude": -117.1202,
                        "metro_code": "San Diego, CA",
                        "postal_code": "92129",
                        "region_code": "CA",
                        "time_zone": "America/Los_Angeles",
                    },
                    "sourceipgeopoint": "32.9661,-117.1202",
                },
                "category": "authentication",
                "hostname": "https://auth.website.auth0.com/api/v2/logs",
                "processid": "21817",
                "processname": "/opt/mozdef/envs/mozdef/cron/auth02mozdef.py",
                "severity": "INFO",
                "summary": "Success Login tester@website.com",
                "tags": ["auth0"],
                "utctimestamp": "2020-04-22T21:31:36.713494+00:00",
                "timestamp": "2020-04-22T21:31:36.713494+00:00",
                "type": "event",
                "mozdef": {
                    "plugins": [
                        "ipFixup", "geoip"
                    ]
                },
                "source": "UNKNOWN",
            },
            "documentid": "Kd7No3EBh9xp2NOIqT6x",
        },
        {
            "documentindex": "events-20200422",
            "documentsource": {
                "receivedtimestamp": "2020-04-22T21:36:01.405116+00:00",
                "mozdefhostname": "mozdef.website.com",
                "details": {
                    "access_device": {
                        "hostname": None,
                        "ip": "1.2.3.4",
                        "location": {
                            "city": "Fontana",
                            "country": "United States",
                            "state": "California",
                        },
                    },
                    "alias": "",
                    "application": {
                        "key": "DI1MFG5M5N5GZIEBVCY2",
                        "name": "Mozilla Auth0 Prod",
                    },
                    "auth_device": {
                        "ip": "1.2.3.4",
                        "location": {
                            "city": "Fontana",
                            "country": "United States",
                            "state": "California",
                        },
                        "name": "858-472-2244",
                    },
                    "email": "",
                    "event_type": "authentication",
                    "factor": "duo_push",
                    "isotimestamp": "2020-04-22T15:05:27.410180+00:00",
                    "reason": "user_approved",
                    "result": "success",
                    "sourceipaddress": "1.2.3.4",
                    "success": True,
                    "txid": "ce2e7158-f1a3-4b34-8488-3ccaf39ca30d",
                    "userkey": "DU3WROU2UXE8NA7138EL",
                    "username": "tester@website.com",
                    "sourceipv4address": "1.2.3.4",
                    "sourceipgeolocation": {
                        "city": "Anaheim",
                        "continent": "NA",
                        "country_code": "US",
                        "country_name": "United States",
                        "dma_code": 803,
                        "latitude": 33.8405,
                        "longitude": -117.9526,
                        "metro_code": "Anaheim, CA",
                        "postal_code": "92801",
                        "region_code": "CA",
                        "time_zone": "America/Los_Angeles",
                    },
                    "sourceipgeopoint": "33.8405,-117.9526",
                },
                "category": "authentication",
                "hostname": "mozdef.website.com",
                "processid": "10391",
                "processname": "/opt/mozdef/envs/mozdef/cron/duo_logpull.py",
                "severity": "INFO",
                "summary": "authentication success for tester@website.com",
                "tags": ["duosecurity"],
                "utctimestamp": "2020-04-22T21:36:01.405116+00:00",
                "timestamp": "2020-04-22T21:36:01.405116+00:00",
                "type": "event",
                "mozdef": {
                    "plugins": [
                        "ipFixup", "geoip"
                    ]
                },
                "source": "UNKNOWN",
            },
            "documentid": "497Ro3EBh9xp2NOIs0Sk",
        },
        {
            "documentindex": "events-20200422",
            "documentsource": {
                "receivedtimestamp": "2020-04-22T21:36:01.689772+00:00",
                "mozdefhostname": "mozdef.website.com",
                "details": {
                    "clientid": "TnqNECyCfoQYd1X7c4xwMF4PMsEfyWPj",
                    "clientname": "website.zoom.us",
                    "connection": "Mozilla-LDAP",
                    "description": "None",
                    "eventname": "Success Login",
                    "messageid": "5ea05d38d28ace0714820128",
                    "raw": "{'_id': '5ea05d38d28ace0714820128', 'date': '2020-04-22T15:05:28.374Z', 'type': 's', 'description': 'None', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'client_id': 'TnqNECyCfoQYd1X7c4xwMF4PMsEfyWPj', 'client_name': 'website.zoom.us', 'ip': '1.2.3.4', 'client_ip': 'None', 'user_agent': 'Firefox Mobile 75.0.0 / Android 0.0.0', 'details': {'prompts': [{'name': 'lock-password-authenticate', 'initiatedAt': '1587567915617', 'completedAt': '1587567915964', 'connection': 'Mozilla-LDAP', 'connection_id': 'con_dc6SPKopkKT33i70', 'strategy': 'ad', 'identity': 'Mozilla-LDAP|tester', 'stats': {'loginsCount': '2314'}, 'session_user': '5ea05d2b5441aa04697bbe2e', 'elapsedTime': '347'}, {'name': 'login', 'flow': 'login', 'initiatedAt': '1587567905584', 'completedAt': '1587567915965', 'timers': {'rules': '386'}, 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'elapsedTime': '10381'}, {'name': 'mfa', 'flow': 'mfa', 'initiatedAt': '1587567916358', 'completedAt': '1587567928352', 'performed_acr': ['http://schemas.openid.net/pape/policies/2007/06/multi-factor'], 'performed_amr': ['mfa'], 'provider': 'duo', 'elapsedTime': '11994'}], 'initiatedAt': '1587567905582', 'completedAt': '1587567928372', 'elapsedTime': '22790', 'session_id': 'xUneHabcm83WvtggcG-csaKqfjUCY9Uw', 'device_id': 'v0:88c38ae0-343c-11ea-888a-8fb9710d9719', 'stats': {'loginsCount': '2314'}}, 'hostname': 'auth.website.auth0.com', 'user_id': 'ad|Mozilla-LDAP|tester', 'user_name': 'tester@website.com', 'strategy': 'ad', 'strategy_type': 'enterprise', 'isMobile': 'True'}",
                    "sourceipaddress": "1.2.3.4",
                    "success": True,
                    "useragent": "Firefox Mobile 75.0.0 / Android 0.0.0",
                    "userid": "ad|Mozilla-LDAP|tester",
                    "username": "tester@website.com",
                    "sourceipv4address": "1.2.3.4",
                    "sourceipgeolocation": {
                        "city": "Anaheim",
                        "continent": "NA",
                        "country_code": "US",
                        "country_name": "United States",
                        "dma_code": 803,
                        "latitude": 33.8405,
                        "longitude": -117.9526,
                        "metro_code": "Anaheim, CA",
                        "postal_code": "92801",
                        "region_code": "CA",
                        "time_zone": "America/Los_Angeles",
                    },
                    "sourceipgeopoint": "33.8405,-117.9526",
                },
                "category": "authentication",
                "hostname": "https://auth.website.auth0.com/api/v2/logs",
                "processid": "9101",
                "processname": "/opt/mozdef/envs/mozdef/cron/auth02mozdef.py",
                "severity": "INFO",
                "summary": "Success Login tester@website.com",
                "tags": ["auth0"],
                "utctimestamp": "2020-04-22T21:36:01.689772+00:00",
                "timestamp": "2020-04-22T21:36:01.689772+00:00",
                "type": "event",
                "mozdef": {
                    "plugins": [
                        "ipFixup", "geoip"
                    ]
                },
                "source": "UNKNOWN",
            },
            "documentid": "Jd7Ro3EBh9xp2NOItEXH",
        },
    ],
    "channel": None,
    "status": "manual",
    "classname": "AlertGeoModel",
    "details": {
        "username": "tester@website.com",
        "hops": [
            {
                "origin": {
                    "ip": "1.2.3.4",
                    "city": "Anaheim",
                    "country": "US",
                    "latitude": 33.8405,
                    "longitude": -117.9526,
                    "observed": datetime.datetime(2020, 4, 22, 21, 31, 35, 852684),
                    "geopoint": "33.8405,-117.9526",
                },
                "destination": {
                    "ip": "4.3.2.1",
                    "city": "San Diego",
                    "country": "US",
                    "latitude": 32.9661,
                    "longitude": -117.1202,
                    "observed": datetime.datetime(2020, 4, 22, 21, 31, 36, 427461),
                    "geopoint": "32.9661,-117.1202",
                },
            },
            {
                "origin": {
                    "ip": "4.3.2.1",
                    "city": "San Diego",
                    "country": "US",
                    "latitude": 32.9661,
                    "longitude": -117.1202,
                    "observed": datetime.datetime(2020, 4, 22, 21, 31, 36, 713494),
                    "geopoint": "32.9661,-117.1202",
                },
                "destination": {
                    "ip": "1.2.3.4",
                    "city": "Anaheim",
                    "country": "US",
                    "latitude": 33.8405,
                    "longitude": -117.9526,
                    "observed": datetime.datetime(2020, 4, 22, 21, 36, 1, 405116),
                    "geopoint": "33.8405,-117.9526",
                },
            },
        ],
        "sourceipaddress": "4.3.2.1",
        "sourceipv4address": "4.3.2.1",
        "factors": [
            {
                "asn_hops": [
                    (
                        {
                            "autonomous_system_number": 21928,
                            "autonomous_system_organization": "T-MOBILE-AS21928",
                        },
                        {
                            "autonomous_system_number": 20001,
                            "autonomous_system_organization": "TWC-20001-PACWEST",
                        },
                    )
                ]
            }
        ],
    },
    "notify_mozdefbot": True,
}


class TestDict2List(UnitTestSuite):
    def test_simple_input(self):
        test_input = {
            'test': {
                'values': [
                    {
                        'thing': ('value1', 32),
                        'other': ('value2', 100),
                    },
                    {
                        'thing': ('value1', -10),
                        'other': ('value2', 1),
                    }
                ],
            },
            ('complex', 'key'): True,
            'count': 100,
            'time': datetime.datetime.utcnow(),
            'error': None,
        }

        flattened = list(dict2List(test_input))

        # We can't guarantee the order that keys and values will be pulled out
        # in so instead of doing a comparison to the list we might expect,
        # we test the interface of the function.
        assert all([
            isinstance(value, (str, int, float, bool, type(None)))
            for value in flattened
        ])
        assert len(set(flattened)) > 0

    def test_geomodel_alert(self):
        flattened = list(dict2List(TEST_ALERT))

        assert all([
            isinstance(value, (str, int, float, bool, type(None)))
            for value in flattened
        ])
        assert len(set(flattened)) > 0
