'''Representations for data models used by geomodel.

MozDef currently uses Python3.6 and so, at present, these models
are represented as dictionaries with validator functions.
'''

from datetime import datetime
from urllib.parse import urlparse


def _is_valid_ipv4(ip):
    octets = ip.split('.')

    try:
        return len(octets) == 4 and all([
            0 <= int(octet) <= 255
            for octet in octets
        ])
    except ValueError:
        return False


def _is_str(s):
    return isinstance(s, str)


def _is_recent_datetime(fmt_date_str):
    try:
        dt = datetime.strptime(fmt_date_str, '%Y-%m-%d %H:%M:%S.%f')
    except ValueError:
        return False

    return dt.year >= 2019


def _is_valid_latitude(lat):
    try:
        return -90.0 <= float(lat) <= 90.0
    except ValueError:
        return False


def _is_valid_longitude(lon):
    try:
        return -180.0 <= float(lon) <= 180.0
    except ValueError:
        return False


def _is_url(url):
    parsed = urlparse(url)
    return parsed.scheme != '' and parsed.netloc != ''


def _match_shape(dictionary, match):
    # `match` is a dictionary shaped like:
    # { 'key': predicate, 'key2': { 'key3': predicate } }
    # where each `predicate` is a function that accepts the expected value
    # corresponding to each key that validates that value.
    try:
        return all([
            match[key](dictionary.get(key)) if \
                    not isinstance(match[key], dict) \
                    else _match_shape(dictionary.get(key), match[key])
            for key in match
        ])
    except AttributeError:
        return False


def validate_configuration(config):
    '''Validate that a top-level configuration for GeoModel conforms to the
    expected format and value restrictions.
    '''

    return _match_shape(config, {
        'elasticSearchAddress': _is_url,
        'localities': {
            'index': _is_str,
            'validDurationDays': lambda hours: int(hours) > 0,
            'radiusKilometres': lambda radius: float(radius) > 0.0,
        },
        'events': {
            'index': _is_str,
            'searchWindow': {
                'minutes': lambda mins: int(mins) > 0,
            },
            'queries': lambda queries: all([
                _match_shape(query, {
                    'lucene': _is_str,
                    'username': _is_str
                })
                for query in queries
            ])
        },
        'alerts': {
            'index': _is_str,
        }
    })


def validate_locality_state(state):
    '''Validate that a locality state record conforms to the expected format
    and value restrictions.
    '''

    return _match_shape(state, {
        'username': _is_str,
        'localities': lambda localities: all([
            _match_shape(locality, {
                'sourceipv4address': _is_valid_ipv4,
                'city': _is_str,
                'country': _is_str,
                'lastaction': _is_recent_datetime,
                'latitude': _is_valid_latitude,
                'longitude': _is_valid_longitude,
                'radius': lambda radius: float(radius) > 0.0
            })
            for locality in localities
        ])
    })


def validate_alert(alert):
    '''Validates that an alert conforms the the expected format and value
    restrictions.
    '''

    return _match_shape(alert, {
        'source': lambda s: s == 'geomodel',
        'category': lambda c: c == 'geomodel',
        'type': lambda t: t == 'geomodel',
        'username': _is_str,
        'sourceipv4address': _is_valid_ipv4,
        'timestamp': _is_recent_datetime,
        'origin': {
            'city': _is_str,
            'country': _is_str,
            'latitude': _is_valid_latitude,
            'longitude': _is_valid_longitude
        },
        'tags': lambda tags: tags == ['geomodel'],
        'summary': _is_str
    })
