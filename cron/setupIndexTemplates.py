#!/usr/bin/env python
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Use this to setup the index templates for mozdef
# You only need to run it once, it will setup the templates
# used as future indexes are created

import requests
import sys
from configlib import getConfig, OptionParser


def esPutTemplates():
    eventstemplate = r'''
    {
        "template" : "events*",
        "mappings" : {
          "event" : {
            "properties" : {
              "category" : {
                "index" : "not_analyzed",
                "type" : "string"
              },
              "details" : {
                "properties" : {
                  "destinationipaddress" : {
                    "type" : "ip"
                  },
                  "destinationport" : {
                    "type" : "string"
                  },
                  "dn" : {
                    "type" : "string"
                  },
                  "hostname" : {
                    "type" : "string"
                  },
                  "msg" : {
                    "type" : "string"
                  },
                  "note" : {
                    "type" : "string"
                  },
                  "processid" : {
                    "type" : "string"
                  },
                  "program" : {
                    "type" : "string"
                  },
                  "protocol" : {
                    "type" : "string"
                  },
                  "result" : {
                    "type" : "string"
                  },
                  "source" : {
                    "type" : "string"
                  },
                  "sourceipaddress" : {
                    "type" : "ip"
                  },
                  "sourceport" : {
                    "type" : "string"
                  },
                  "srcip" : {
                    "type" : "ip"
                  },
                  "sub" : {
                    "type" : "string"
                  },
                  "success" : {
                    "type" : "boolean"
                  },
                  "timestamp" : {
                    "type" : "string"
                  },
                  "ts" : {
                    "type" : "string"
                  },
                  "uid" : {
                    "type" : "string"
                  }
                }
              },
              "eventsource" : {
                "type" : "string"
              },
              "hostname" : {
                "type" : "string"
              },
              "processid" : {
                "type" : "string"
              },
              "receivedtimestatmp" : {
                "type" : "date",
                "format" : "dateOptionalTime"
              },
              "severity" : {
                "type" : "string"
              },
              "summary" : {
                "type" : "string"
              },
              "tags" : {
                "index" : "not_analyzed",
                "type" : "string"
              },
              "timestamp" : {
                "type" : "date",
                "format" : "dateOptionalTime"
              },
              "utctimestamp" : {
                "type" : "date",
                "format" : "dateOptionalTime"
              }
            }
          }
        }
    }
    '''
    url = '{0}/_template/eventstemplate'.format(options.esservers[0])
    r = requests.put(url=url, data=eventstemplate)
    if r.status_code == 200:
        print('Successfully put events template')
    else:
        print('Problem putting events template %r' % r)

    alertstemplate = r'''
    {
        "template" : "alerts*",
        "mappings" : {
              "alert" : {
                "properties" : {
                  "timestamp" : {
                    "format" : "dateOptionalTime",
                    "type" : "date"
                  },
                  "tags" : {
                    "type" : "string"
                  },
                  "summary" : {
                    "type" : "string"
                  },
                  "receivedtimestatmp" : {
                    "format" : "dateOptionalTime",
                    "type" : "date"
                  },
                  "category" : {
                    "index" : "not_analyzed",
                    "type" : "string"
                  },
                  "events" : {
                    "properties" : {
                      "id" : {
                        "type" : "string"
                      },
                      "index" : {
                        "type" : "string"
                      },
                      "type" : {
                        "type" : "string"
                      }
                    }
                  },
                  "eventsource" : {
                    "type" : "string"
                  },
                  "hostname" : {
                    "type" : "string"
                  },
                  "severity" : {
                    "type" : "string"
                  },
                  "utctimestamp" : {
                    "format" : "dateOptionalTime",
                    "type" : "date"
                  }
                }
              }
        }
    }
    '''

    url = '{0}/_template/alertstemplate'.format(options.esservers[0])
    r = requests.put(url=url, data=alertstemplate)
    if r.status_code == 200:
        print('Successfully put alerts template')
    else:
        print('Problem putting alerts template %r' % r)


def initConfig():
    options.esservers = list(getConfig(
        'esservers',
        'http://localhost:9200',
        options.configfile).split(',')
        )

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-c",
                      dest='configfile',
                      default=sys.argv[0].replace('.py', '.conf'),
                      help="configuration file to use")
    (options, args) = parser.parse_args()
    initConfig()
    esPutTemplates()
