Introduction
============

Concept of operations
----------------------
Event Management
****************
From an event management point of view MozDef relies on Elastic Search for:

* event storage
* event archiving
* event indexing
* event searching

This means if you use MozDef for your log management you can use the features of Elastic Search to store millions of events, archive them to Amazon if needed,
index the fields of your events, and search them using highly capable interfaces like Kibana.

MozDef differs from other log management solutions that use Elastic Search in that it does not allow your log shippers direct contact with Elastic Search itself.
In order to provide advanced functionality like event correlation, aggregation and machine learning, MozDef inserts itself as a shim between your log shippers (rsyslog, syslog-ng, beaver, nxlog, heka, logstash)
and Elastic Search. This means your log shippers interact with MozDef directly and MozDef handles translating their events as they make they're way to Elastic Search.

Event Pipeline
***************
The logical flow of events is:

::


                                      +–––––––––––+              +––––––––––––––+
                                      |    MozDef +––––––––––––––+              |
                   +––––––––––+       |    FrontEnd              | Elastic      |
                   | shipper  +–––––––+–––––––––––+              | Search       |
                   ++++++++++++                                  | cluster      |
                   ++++++++++++                                  |              |
                   | shipper  +–––––––+–––––––––––+              |              |
                   +––––––––––+       |    MozDef +-–––––––––––––+              |
                                      |    FrontEnd              |              |
                                      +–––––––––––+              |              |
                                                                 +––––––––––––––+


Choose a shipper (logstash, nxlog, beaver, heka, rsyslog, etc) that can send JSON over http(s). MozDef uses nginx to provide http(s) endpoints that accept JSON posted
over http. Each front end contains a Rabbit-MQ message queue server that accepts the event and sends it for further processing.

You can have as many front ends, shippers and cluster members as you with in any geographic organization that makes sense for your topology. Each front end runs a series
of python workers hosted by uwsgi that perform:

* event normalization (i.e. translating between shippers to a common taxonomy of event data types and fields)
* event enrichment
* simple regex-based alerting
* machine learning on the real-time event stream

Event Enrichment
****************
To facilitate event correlation, MozDef allows you to write plugins to populate your event data with consistent meta-data customized for your environment. Through simple
python plug-ins this allows you to accomplish a variety of event-related tasks like: 

* further parse your events into more details
* geoIP tag your events
* correct fields not properly handled by log shippers
* tag all events involving key staff
* tag all events involving previous attackers or hits on a watchlist
* tap into your event stream for ancilary systems
* maintain 'last-seen' lists for assets, employees, attackers

Event Correlation/Alerting
**************************
Correlation/Alerting is currently handled as a series of queries run periodically against the Elastic Search engine. This allows MozDef to make full use of the lucene
query engine to group events together into summary alerts and to correlate across any data source accessible to python.

Incident Handling
*****************
From an incident handling point of view MozDef offers the realtime responsiveness of Meteor in a web interface. This allows teams of incident responders the ability
to see each others actions in realtime, no matter their physical location. 
