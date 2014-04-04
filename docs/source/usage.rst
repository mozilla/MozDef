Usage
=====

Sending logs to MozDef
----------------------

Events/Logs are accepted as json over http(s) or over rabbit-mq. Most modern log shippers support json output. MozDef is tested with support for: 

* heka ( https://github.com/mozilla-services/heka ) 
* beaver ( https://github.com/josegonzalez/beaver )
* nxlog ( http://nxlog-ce.sourceforge.net/ )
* logstash ( http://logstash.net/ )
* native python code ( https://github.com/jeffbryner/MozDef/blob/master/lib/mozdef.py or  https://github.com/jeffbryner/MozDef/blob/master/test/json2Mozdef.py )
* AWS cloudtrail (via native python)


Web Interface
-------------

MozDef uses the Meteor framework  ( https://www.meteor.com/ ) for the web interface and bottle.py for the REST API. 
For authentication, MozDef ships with native support for Persona ( https://login.persona.org/about ). 
Meteor (the underlying UI framework) also supports many authentication options ( http://docs.meteor.com/#accounts_api ) including google, github, twitter, facebook, oath, native accounts, etc.


Events visualizations
*********************

Since the backend of MozDef is Elastic Search, you get all the goodness of Kibana with little configuration.
The MozDef UI is focused on incident handling and adding security-specific visualizations of SIEM data to help you weed through the noise.


Alerts
******

Alerts are generally implemented as Elastic Search searches, or realtime examination of the incoming message queues. MozDef provides a plugin interface to allow open access to event data for enrichment, hooks into other systems, etc. 


Incident handling
*****************
