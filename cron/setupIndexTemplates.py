#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

# Use this to setup the index templates for mozdef
# You only need to run it once, it will setup the templates
# used as future indexes are created

import requests
import sys
from configlib import getConfig, OptionParser


def esPutTemplates():
    eventstemplate = r'''
	{
	    "template":"events*",
	    "mappings":{
	        "event":{
	            "_all" : {"enabled" : true},
	            "dynamic_templates" : [ {
	                "string_fields" : {
	                    "match" : "*",
	                    "match_mapping_type" : "string",
	                    "mapping" : {
	                        "type" : "multi_field",
	                        "fields" : {
	                            "{name}" : {"type": "string", "index" : "analyzed", "omit_norms" : true },
	                            "raw" : {"type": "string", "index" : "not_analyzed", "ignore_above" : 256}
	                        }
	                    }
	                }
	            } ],
	            "properties":{
	                "category":{
	                  "index":"not_analyzed",
	                  "type":"string"
	                },
	                "details":{
	                  "properties":{
	                    "destinationipaddress":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "destinationipaddress" : {"type" : "ip"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "destinationport":{
	                      "type":"string"
	                    },
	                    "dn":{
	                      "type":"string"
	                    },
	                    "hostname":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "hostname": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "msg":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "msg": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "note":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "note": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "processid":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "processid": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "program":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "program": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "protocol":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "protocol": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "result":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "result": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "source":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "source": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "sourceipaddress":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "sourceipaddress": {"type": "ip"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "sourceport":{
	                      "type":"string"
	                    },
	                    "sub":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "sub": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    },
	                    "success":{
	                      "type":"boolean"
	                    },
	                    "timestamp":{
	                      "type":"string"
	                    },
	                    "ts":{
	                      "type":"string"
	                    },
	                    "uid":{
	                      "type" : "multi_field",
	                      "fields" : {
	                        "uid": {"type": "string"},
	                        "raw" : {"type" : "string", "index" : "not_analyzed"}
	                      }
	                    }
	                  }
	                },
	                "eventsource":{
	                  "type" : "multi_field",
	                  "fields" : {
	                    "eventsource": {"type": "string"},
	                    "raw" : {"type" : "string", "index" : "not_analyzed"}
	                  }
	                },
	                "hostname":{
	                  "type" : "multi_field",
	                  "fields" : {
	                    "hostname": {"type": "string"},
	                    "raw" : {"type" : "string", "index" : "not_analyzed"}
	                  }
	                },
	                "processid":{
	                  "type" : "multi_field",
	                  "fields" : {
	                    "processid": {"type": "string"},
	                    "raw" : {"type" : "string", "index" : "not_analyzed"}
	                  }
	                },
	                "receivedtimestatmp":{
	                  "type":"date",
	                  "format":"dateOptionalTime"
	                },
	                "severity":{
	                  "type" : "multi_field",
	                  "fields" : {
	                    "severity": {"type": "string"},
	                    "raw" : {"type" : "string", "index" : "not_analyzed"}
	                  }
	                },
	                "summary":{
	                  "type" : "multi_field",
	                  "fields" : {
	                    "summary": {"type": "string"},
	                    "raw" : {"type" : "string", "index" : "not_analyzed"}
	                  }
	                },
	                "tags":{
	                  "type" : "multi_field",
	                  "fields" : {
	                    "tags": {"type": "string"},
	                    "raw" : {"type" : "string", "index" : "not_analyzed"}
	                  }
	                },
	                "timestamp":{
	                  "type":"date",
	                  "format":"dateOptionalTime"
	                },
	                "utctimestamp":{
	                  "type":"date",
	                  "format":"dateOptionalTime"
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
	  "template":"alerts*",
	  "mappings":{
	    "alert":{
	      "properties":{
	        "timestamp":{
	          "format":"dateOptionalTime",
	          "type":"date"
	        },
	        "tags":{
	          "type" : "multi_field",
	          "fields" : {
	            "tags": {"type": "string"},
	            "raw" : {"type" : "string", "index" : "not_analyzed"}
	          }
	        },
	        "summary":{
	          "type" : "multi_field",
	          "fields" : {
	            "summary": {"type": "string"},
	            "raw" : {"type" : "string", "index" : "not_analyzed"}
	          }
	        },
	        "receivedtimestatmp":{
	          "format":"dateOptionalTime",
	          "type":"date"
	        },
	        "category":{
	          "type" : "multi_field",
	          "fields" : {
	            "category": {"type": "string"},
	            "raw" : {"type" : "string", "index" : "not_analyzed"}
	          }
	        },
	        "events":{
	          "properties":{
	            "id":{
	              "type":"string"
	            },
	            "index":{
	              "type":"string"
	            },
	            "type":{
	              "type":"string"
	            }
	          }
	        },
	        "eventsource":{
	          "type" : "multi_field",
	          "fields" : {
	            "eventsource": {"type": "string"},
	            "raw" : {"type" : "string", "index" : "not_analyzed"}
	          }
	        },
	        "hostname":{
	          "type" : "multi_field",
	          "fields" : {
	            "hostname": {"type": "string"},
	            "raw" : {"type" : "string", "index" : "not_analyzed"}
	          }
	        },
	        "severity":{
	          "type" : "multi_field",
	          "fields" : {
	            "severity": {"type": "string"},
	            "raw" : {"type" : "string", "index" : "not_analyzed"}
	          }
	        },
	        "utctimestamp":{
	          "format":"dateOptionalTime",
	          "type":"date"
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
