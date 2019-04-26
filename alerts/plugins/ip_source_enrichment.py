# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation


CONFIG_FILE = './ip_source_enrichment.json.conf'


def _load_config(file_path):
    '''Private

    Read and parse a file from disk as JSON into a dictionary.
    '''

    return {}


class _RegexMatchRule(object):
    '''Private

    A rule defining a mapping from a regular expression matching a
    set of IP addresses to a format string accepting one parameter.

    Produced by EnrichIPs given a plugin configuration.
    '''

    def __init__(self, regex, fmt):
        '''Initialize the rule with a regular expression and
        format string.
        '''

        self._ip_regex = regex
        self._format_string = fmt


    def matches(self, input_str):
        '''Produces a list of strings each produced by formatting
        the configured format string with any IPs found in the
        provided input.
        '''

        return []


class _CIDRMatchRule(object):
    '''Private

    A rule defining a mapping from a CIDR address to a format string
    that accepts one parameter.

    Produced by EnrichIPs given a plugin configuration.
    '''
   
    def __init__(self, cidr_str, fmt):
        '''Initialize the rule with an IPv4 or IPv6 CIDR address
        string and format string.
        '''

        self._cidr = cidr_str
        self._format_string = fmt

        
    def matches(self, input_str):
        '''Produces a list of strings each produced by formatting
        the configured format string with any IPs found in the
        provided input.
        '''

        return []


class EnrichIPs(object):
    '''Add information to alerts containing IP addresses that describes
    the source location of the IP address if it can be determined based
    on a configured mapping.
    '''

    def __init__(self):
        '''Initialize the plugin from a configuration in preparation to
        match alerts.
        '''

        self.configuration = _load_config(CONFIG_FILE)


    def enrich(self, alert):
        '''Enrich alerts containing IP addresses with information about
        the location from which those IPs originate.
        Returns a modified alert.
        '''

        return alert
