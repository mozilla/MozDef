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


JSON format
-----------

This section describes the structure JSON objects to be sent to MozDef.
Using this standard ensures developers, admins, etc are configuring their application or system to be easily integrated into MozDef.

Background
**********

Mozilla used CEF as a logging standard for compatibility with Arcsight and for standardization across systems. While CEF is an admirable standard, MozDef prefers JSON logging for the following reasons:

* Every development language can create a JSON structure
* JSON is easily parsed by computers/programs which are the primary consumer of logs
* CEF is primarily used by Arcsight and rarely seen outside that platform and doesn't offer the extensibility of JSON
* A wide variety of log shippers (heka, logstash, fluentd, nxlog, beaver) are readily available to meet almost any need to transport logs as JSON.
* JSON is already the standard for cloud platforms like amazon's cloudtrail logging

Description
***********

As there is no common RFC-style standard for json logs, we prefer the following structure adapted from a combination of the graylog GELF and logstash specifications.

Note all fields are lowercase to avoid one program sending sourceIP, another sending sourceIp, another sending SourceIPAddress, etc.
Since the backend for MozDef is elasticsearch and fields are case-sensitive this will allow for easy compatibility and reduce potential confusion for those attempting to use the data.
MozDef will perform some translation of fields to a common schema but this is intended to allow the use of heka, nxlog, beaver and retain compatible logs.

Mandatory Fields
****************

+------------+-------------------------------------+-----------------------------------+
|    Field   |             Purpose                 |            Sample Value           |
+============+=====================================+===================================+
| category   | General category/type of event      | Authentication, Authorization,    |
|            | matching the 'what should I log'    | Account Creation, Shutdown,       |
|            | section below                       | Startup, Account Deletion,        |
|            |                                     | Account Unlock, brointel,         |
|            |                                     | bronotice                         |
+------------+-------------------------------------+-----------------------------------+
| details    | Additional, event-specific fields   | "dn": "john@example.com,o=com,    |
|            | that you would like included with   | dc=example", "facility": "daemon" |
|            | the event. Please completely spell  |                                   |
|            | out a field rather an abbreviate:   |                                   |
|            | i.e. sourceipaddress instead of     |                                   |
|            | srcip.                              |                                   |
+------------+-------------------------------------+-----------------------------------+
| hostname   | The fully qualified domain name of  | server1.example.com               |
|            | the host sending the message        |                                   |
+------------+-------------------------------------+-----------------------------------+
| processid  | The PID of the process sending the  | 1234                              |
|            | log                                 |                                   |
+------------+-------------------------------------+-----------------------------------+
|processname | The name of the process sending the | myprogram.py                      |
|            | log                                 |                                   |
+------------+-------------------------------------+-----------------------------------+
| severity   | RFC5424 severity level of the event | INFO                              |
|            | in all caps: DEBUG, INFO, NOTICE,   |                                   |
|            | WARNING, ERROR, CRITICAL, ALERT,    |                                   |
|            | EMERGENCY                           |                                   |
+------------+-------------------------------------+-----------------------------------+
| source     | Source of the event (file name,     | /var/log/syslog/2014.01.02.log    |
|            | system name, component name)        |                                   |
+------------+-------------------------------------+-----------------------------------+
| summary    | Short human-readable version of the | john login attempts over          |
|            | event suitable for IRC, SMS, etc.   | threshold, account locked         |
+------------+-------------------------------------+-----------------------------------+
| tags       | An array or list of any tags you    | vpn, audit                        |
|            | would like applied to the event     |                                   |
|            |                                     | nsm,bro,intel                     |
+------------+-------------------------------------+-----------------------------------+
| timestamp  | Full date plus time timestamp of    | 2014-01-30T19:24:43+00:00         |
|            | the event in ISO format including   |                                   |
|            | the timezone offset                 |                                   |
+------------+-------------------------------------+-----------------------------------+

Details substructure (optional fields)
**************************************

+----------------------+--------------------------+---------------+------------------------------+
|        Field         |         Purpose          |   Used In     |       Sample Value           |
+======================+==========================+===============+==============================+
| destinationipaddress | Destination IP of a      | NSM/Bro/Intel | 8.8.8.8                      |
|                      | network flow             |               |                              |
+----------------------+--------------------------+---------------+------------------------------+
| destinationport      | Destination port of a    | NSM/Bro/Intel | 80                           |
|                      | network flow             |               |                              |
+----------------------+--------------------------+---------------+------------------------------+
| dn                   | Distinguished Name in    | event/ldap    | john@example.org,o=org,      |
|                      | LDAP, mean unique ID in  |               | dc=example                   |
|                      | the ldap hierarchy       |               |                              |
+----------------------+--------------------------+---------------+------------------------------+
| filedesc             |                          | NSM/Bro/Intel |                              |
+----------------------+--------------------------+---------------+------------------------------+
| filemimetype         |                          | NSM/Bro/Intel |                              |
+----------------------+--------------------------+---------------+------------------------------+
| fuid                 |                          | NSM/Bro/Intel |                              |
+----------------------+--------------------------+---------------+------------------------------+
| result               | Result of an event,      | event/ldap    | LDAP_SUCCESS                 |
|                      | success or failure       |               |                              |
+----------------------+--------------------------+---------------+------------------------------+
| seenindicator        | Intel indicator that     | NSM/Bro/Intel | evil.com/setup.exe           |
|                      | matched as seen by our   |               |                              |
|                      | system                   |               |                              |
+----------------------+--------------------------+---------------+------------------------------+
| seenindicator_type   | Type of intel indicator  | NSM/Bro/Intel | HTTP::IN_URL                 |
+----------------------+--------------------------+---------------+------------------------------+
| seenwhere            | Where the intel indicator| NSM/Bro/Intel | Intel::URL                   |
|                      | matched (which protocol, |               |                              |
|                      | which field)             |               |                              |
+----------------------+--------------------------+---------------+------------------------------+
| source               | Source of the connection | event/ldap    | Mar 19 15:36:25 ldap1        |
|                      |                          |               | slapd[31031]: conn=6633594   |
|                      |                          |               | fd=49 ACCEPT                 |
|                      |                          |               | from IP=10.54.70.109:23957   |
|                      |                          |               | (IP=0.0.0.0:389)             |
|                      |                          |               |                              |
|                      |                          |               | Mar 19 15:36:25 ldap1        |
|                      |                          |               | slapd[31031]: conn=6633594   |
|                      |                          |               | op=0 BIND                    |
+----------------------+--------------------------+---------------+------------------------------+
| sourceipaddress      | Source IP of a network   | NSM/Bro/Intel | 8.8.8.8                      |
|                      | flow                     |               |                              |
|                      |                          | event/ldap    |                              |
+----------------------+--------------------------+---------------+------------------------------+
| sourceport           | Source port of a network | NSM/Bro/Intel | 42297                        |
|                      | flow                     |               |                              |
+----------------------+--------------------------+---------------+------------------------------+
| sources              | Source feed              | NSM/Bro/Intel | CIF - need-to-know           |
+----------------------+--------------------------+---------------+------------------------------+
| success              | Auth success             | event/ldap    | True                         |
+----------------------+--------------------------+---------------+------------------------------+
| uid                  | Bro connection uid       | NSM/Bro/Intel | CZqhEs40odso1tFNx3           |
+----------------------+--------------------------+---------------+------------------------------+


Examples
********

.. code-block:: javascript

	{
	    "timestamp": "2014-02-14T11:48:19.035762739-05:00",
	    "hostname": "fedbox",
	    "processname": "/tmp/go-build278925522/command-line-arguments/_obj/exe/log_json",
	    "processid": 3380,
	    "severity": "INFO",
	    "summary": "joe login failed",
	    "category": "authentication",
	    "source": "",
	    "tags": [
	        "MySystem",
	        "Authentication"
	    ],
	    "details": {
	        "user": "joe",
	        "task": "access to admin page /admin_secret_radioactiv",
	        "result": "10 authentication failures in a row"
	    }
	}
