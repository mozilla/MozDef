#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2017 Mozilla Corporation

from lib.alerttask import AlertTask
from query_models import SearchQuery, TermMatch, QueryStringMatch, PhraseMatch
import json
import sys
import re
import netaddr

# This alert requires a configuration file, ssh_lateral.json to exist
# in the alerts directory.
#
# hostmustmatch:
#   List of regex, if one matches the source of the syslog event (e.g. the
#   hostname, it will be considered for an alert.
#
# hostmustnotmatch:
#   Anything in this list will never be considered for an alert, even if it
#   matches hostmustmatch.
#
# alertifsource:
#   If a login occurs on a host matching something in hostmustmatch, and it
#   is from an address in a CIDR block indicated in alertifsource, an alert
#   will be generated.
#
# notalertifsource:
#   Anything source IP matching a network in this list will not be alerted on,
#   even if it matches alertifsource.
#
# ignoreusers:
#   Never generate alerts for a login for a user matching these regex.
#
# exceptions:
#   Exceptions to alerts. Each element in the list should be as follows:
#       [ "user_regex", "host_regex", "cidr" ]
#
#   If a login matches an exception rule, it will not be alerted on.
#
# Example:
#
# {
#     "hostmustmatch": [
#         ".*\\.enterprise\\.mozilla.com"
#     ],
#     "hostmustnotmatch": [
#         "ten-forward\\.enterprise\\.mozilla\\.com"
#     ],
#     "alertifsource": [
#         "10.0.0.0/8"
#     ],
#     "notalertifsource": [
#         "10.0.22.0/24",
#         "10.0.23.0/24"
#     ],
#     "ignoreusers": [
#         ".*@\\S+.*"
#     ],
#     "exceptions": [
#         ["kirk",".*","10.1.1.1/32"],
#         ["kirk",".*","10.1.1.2/32"],
#         ["kirk",".*","10.1.1.3/32"],
#         ["spock","sciencestation.enterprise.mozilla.com","10.0.50.0/24"],
#         ["spock","sciencestation.enterprise.mozilla.com","10.0.51.0/24"],
#         ["spock","sciencestation.enterprise.mozilla.com","10.0.52.0/24"],
#         ["spock","sciencestation.enterprise.mozilla.com","10.0.53.0/24"]
#     ]
# }

class SshLateral(AlertTask):
    def __init__(self):
        AlertTask.__init__(self)
        self._config = self.parse_json_alert_config('ssh_lateral.json')

    def main(self):
        search_query = SearchQuery(minutes=2)
        search_query.add_must([
            TermMatch('category', 'syslog'),
            TermMatch('details.program', 'sshd'),
            PhraseMatch('summary', 'Accepted publickey'),
        ])

        self.filtersManual(search_query)
        self.searchEventsAggregated('details.hostname', samplesLimit=10)
        self.walkAggregations(threshold=1)

    # Returns true if the user, host, and source IP fall into an exception
    # listed in the configuration file.
    def exception_check(self, user, host, srcip):
        for x in self._config['exceptions']:
            if re.match(x[0], user) != None and \
                re.match(x[1], host) != None and \
                netaddr.IPAddress(srcip) in netaddr.IPNetwork(x[2]):
                return True
        return False

    def onAggregation(self, aggreg):
        category = 'session'
        severity = 'WARNING'
        tags = ['sshd', 'syslog']

        # Determine if this source host is in scope, first match against
        # hostmustmatch, and then negate matches using hostmustnotmatch
        if len(aggreg['events']) == 0:
            return None
        srchost = aggreg['events'][0]['_source']['details']['hostname']
        srcmatch = False
        for x in self._config['hostmustmatch']:
            if re.match(x, srchost) != None:
                srcmatch = True
                break
        if not srcmatch:
            return None
        for x in self._config['hostmustnotmatch']:
            if re.match(x, srchost) != None:
                return None

        # Determine if the origin of the connection was from a source outside
        # of the exception policy, and in our address scope
        candidates = []
        sampleip = None
        sampleuser = None
        for x in aggreg['events']:
            m = re.match('Accepted publickey for (\S+) from (\S+).*', x['_source']['summary'])
            if m != None and len(m.groups()) == 2:
                ipaddr = netaddr.IPAddress(m.group(2))
                for y in self._config['alertifsource']:
                    if ipaddr in netaddr.IPNetwork(y):
                        # Validate it's not excepted in the IP negation list
                        notalertnetwork = False
                        for z in self._config['notalertifsource']:
                            if ipaddr in netaddr.IPNetwork(z):
                                notalertnetwork = True
                                break
                        if notalertnetwork:
                            continue
                        # Check our user ignore list
                        skipuser = False
                        for z in self._config['ignoreusers']:
                            if re.match(z, m.group(1)):
                                skipuser = True
                                break
                        if skipuser:
                            continue
                        # Check our exception list
                        if self.exception_check(m.group(1), srchost, m.group(2)):
                            continue
                        if sampleip == None:
                            sampleip = m.group(2)
                        if sampleuser == None:
                            sampleuser = m.group(1)
                        candidates.append(x)
        if len(candidates) == 0:
            return None

        summary = 'SSH lateral movement outside policy: access to {} from {} as {}'.format(srchost, sampleip, sampleuser)

        return self.createAlertDict(summary, category, tags, aggreg['events'], severity)

