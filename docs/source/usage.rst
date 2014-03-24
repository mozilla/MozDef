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


Web Interface
-------------
MozDef uses the Meteor framework  ( https://www.meteor.com/ ) for the web interface and bottle.py for the REST API. 
For authentication, MozDef ships with native support for Persona ( https://login.persona.org/about ). 
Meteor (the underlying UI framework) also supports many authentication options ( http://docs.meteor.com/#accounts_api ) including google, github, twitter, facebook, oath, native accounts, etc.



Events visualization
********************

Alerts
******

Incident handling
*****************
