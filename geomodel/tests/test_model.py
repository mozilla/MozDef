import unittest

import mozdef_geomodel.model as model


class TestValidateConfiguration(unittest.TestCase):
    def test_valid_input(self):
        assert model.validate_configuration({
            'elasticSearchAddress': 'http://127.0.0.1:5132',
            'localities': {
                'index': 'locality-state',
                'validDurationDays': 32,
                'radiusKilometres': 50.0,
            },
            'events': {
                'index': 'events-*',
                'queries': [
                    {
                        'lucene': 'tags:duo',
                        'username': 'details.user'
                    }
                ]
            },
            'alerts': {
                'index': 'alerts'
            }
        })


    def test_invalid_input(self):
        assert not model.validate_configuration({
            'elasticSearchAddress': 'http://127.0.0.1:5132',
            'localities': {
                'index': 'locality-state',
                'validDurationDays': 32,
                'radiusKilometres': 50.0,
            },
            'events': {
                'index': 'events-*',
                'queries': [
                    {
                        'lucene': 'tags:duo',
                        'username': 'details.user'
                    },
                    {
                        'lucne': 'tags:auth0',  # Key spelled wrong
                        'username': 'details.user'
                    }
                ]
            },
            'alerts': {
                'index': 'alerts'
            }
        })


    def test_malformed(self):
        assert not model.validate_configuration({
            'elasticSearchAddress': 'http://127.0.0.1:5132',
            'localities': {
                'index': 'locality-state',
                'validDurationDays': 32,
                'radiusKilometres': 50.0,
            },
            'events': {
                'index': 'events-*',
                'queries': [
                    {
                        'lucene': 'tags:duo',
                        'username': 'details.user'
                    }
                ]
            },
            'alerts': 32
        })


class TestValidateLocalityState(unittest.TestCase):
    def test_valid_input(self):
        assert model.validate_locality_state({
            'username': 'testuser',
            'localities': [
                {
                    'sourceipv4address': '122.32.50.109',
                    'city': 'San Francisco',
                    'country': 'USA',
                    'lastaction': '2019-07-15 13:02:55.12362',
                    'latitude': 37.773972,
                    'longitude': -122.431297,
                    'radius': 50.0
                },
                {
                    'sourceipv4address': '55.13.62.50',
                    'city': 'Toronto',
                    'country': 'Canada',
                    'lastaction': '2019-07-15 13:05:12.99123',
                    'latitude': 43.70011,
                    'longitude': -79.4163,
                    'radius': 50.0
                }
            ]
        })


    def test_invalid_input(self):
        assert not model.validate_locality_state({
            'username': 'testuser',
            'localities': [
                {
                    'sourceipv4address': '122.32.50.109',
                    'city': 'San Francisco',
                    'country': 'USA',
                    'lastaction': '2019-07-15 13:02:55.12362',
                    'latitude': -437.773972,  # Invalid latitude
                    'longitude': -122.431297,
                    'radius': 50.0
                },
                {
                    'sourceipv4address': '55.13.62.50',
                    'city': 'Toronto',
                    'country': 'Canada',
                    'lastaction': '2019-07-15 13:05:12.99123',
                    'latitude': 43.70011,
                    'longitude': -79.4163,
                    'radius': 50.0
                }
            ]
        })


class TestValidateAlert(unittest.TestCase):
    def test_valid_input(self):
        assert model.validate_alert({
            'source': 'geomodel',
            'category': 'geomodel',
            'type': 'geomodel',
            'username': 'testuser',
            'sourceipv4address': '12.39.55.252',
            'timestamp': '2019-07-15 13:08:32.34123',
            'origin': {
                'city': 'San Francisco',
                'country': 'USA',
                'latitude': 37.773972,
                'longitude': -122.431297
            },
            'tags': ['geomodel'],
            'summary': 'test summary',
        })


    def test_invalid_input(self):
        assert not model.validate_alert({
            'source': 'geomodel',
            'category': 'geomodel',
            'type': 'geomodel',
            'username': 'testuser',
            'sourceipv4address': '1.329.55.257',  # Invalid IP
            'timestamp': '2019-07-15 13:08:32.34123',
            'origin': {
                'city': 'San Francisco',
                'country': 'USA',
                'latitude': 37.773972,
                'longitude': -122.431297
            },
            'tags': ['geomodel'],
            'summary': 'test summary',
        })
