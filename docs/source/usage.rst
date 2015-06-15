Usage
=====


Web Interface
-------------

MozDef uses the `Meteor framework`_ for the web interface and bottle.py for the REST API.
For authentication, MozDef ships with native support for `Persona`_.
Meteor (the underlying UI framework) also supports `many authentication options`_ including google, github, twitter, facebook, oath, native accounts, etc.

.. _Meteor framework: https://www.meteor.com/
.. _Persona: https://login.persona.org/about
.. _many authentication options: http://docs.meteor.com/#accounts_api

Events visualizations
*********************

Since the backend of MozDef is Elastic Search, you get all the goodness of Kibana with little configuration.
The MozDef UI is focused on incident handling and adding security-specific visualizations of SIEM data to help you weed through the noise.


Alerts
******

Alerts are implemented as Elastic Search searches. MozDef provides a plugin interface to allow open access to event data for enrichment, hooks into other systems, etc.


Incident handling
*****************

Sending logs to MozDef
----------------------

Events/Logs are accepted as json over http(s) with the POST or PUT methods or over rabbit-mq.
Most modern log shippers support json output. MozDef is tested with support for:

* `heka`_
* `beaver`_
* `nxlog`_
* `logstash`_
* `native python code`_
* `AWS cloudtrail`_ (via native python)

We have `some configuration snippets`_

.. _heka: https://github.com/mozilla-services/heka
.. _beaver: https://github.com/josegonzalez/beaver
.. _nxlog: http://nxlog-ce.sourceforge.net/
.. _logstash: http://logstash.net/
.. _native python code: https://github.com/gdestuynder/mozdef_lib
.. _AWS cloudtrail: https://aws.amazon.com/cloudtrail/
.. _some configuration snippets: https://github.com/jeffbryner/MozDef/tree/master/examples

What should I log?
******************

If your program doesn't log anything it doesn't exist. If it logs everything that happens it becomes like the proverbial boy who cried wolf. There is a fine line between logging too little and too much but here is some guidance on key events that should be logged and in what detail.

+------------------+---------------------------+---------------------------------------+
|    Event         |         Example           |               Rationale               |
+==================+===========================+=======================================+
| Authentication   | Failed/Success logins     | Authentication is always an important |
| Events           |                           | event to log as it establishes        |
|                  |                           | traceability for later events and     |
|                  |                           | allows correlation of user actions    |
|                  |                           | across systems.                       |
+------------------+---------------------------+---------------------------------------+
| Authorization    | Failed attempts to        | Once a user is authenticated they     |
| Events           | insert/update/delete a    | usually obtain certain permissions.   |
|                  | record or access a        | Logging when a user's permissions do  |
|                  | section of an application.| not allow them to perform a function  |
|                  |                           | helps troubleshooting and can also    |
|                  |                           | be helpful when investigating         |
|                  |                           | security events.                      |
+------------------+---------------------------+---------------------------------------+
| Account          | Account                   | Adding, removing or changing accounts |
| Lifecycle        | creation/deletion/update  | are often the first steps an attacker |
|                  |                           | performs when entering a system.      |
+------------------+---------------------------+---------------------------------------+
| Password/Key     | Password changed, expired,| If your application takes on the      |
| Events           | reset. Key expired,       | responsibility of storing a user's    |
|                  | changed, reset.           | password (instead of using a          |
|                  |                           | centralized source) it is             |
|                  |                           | important to note changes to a users  |
|                  |                           | credentials or crypto keys.           |
+------------------+---------------------------+---------------------------------------+
| Account          | Account lock, unlock,     | If your application locks out users   |
| Activations      | disable, enable           | after failed login attempts or allows |
|                  |                           | for accounts to be inactivated,       |
|                  |                           | logging these events can assist in    |
|                  |                           | troubleshooting access issues.        |
+------------------+---------------------------+---------------------------------------+
| Application      | Invalid input,            | If your application catches errors    |
| Exceptions       | fatal errors,             | like invalid input attempts on web    |
|                  | known bad things          | forms, failures of key components,    |
|                  |                           | etc creating a log record when these  |
|                  |                           | events occur can help in              |
|                  |                           | troubleshooting and tracking security |
|                  |                           | patterns across applications. Full    |
|                  |                           | stack traces should be avoided however|
|                  |                           | as the signal to noise ratio is       |
|                  |                           | often overwhelming.                   |
|                  |                           |                                       |
|                  |                           | It is also preferable to send a single|
|                  |                           | event rather than a multitude of      |
|                  |                           | events if it is possible for your     |
|                  |                           | application to correlate a significant|
|                  |                           | exception.                            |
|                  |                           |                                       |
|                  |                           | For example, some systems are         |
|                  |                           | notorious for sending a connection    |
|                  |                           | event with source IP, then sending an |
|                  |                           | authentication event with a session ID|
|                  |                           | then later sending an event for       |
|                  |                           | invalid input that doesn't include    |
|                  |                           | source IP or session ID or username.  |
|                  |                           | Correctly correlating these events    |
|                  |                           | across time is much more difficult    |
|                  |                           | than just logging all pieces of       |
|                  |                           | information if it is available.       |
+------------------+---------------------------+---------------------------------------+

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
	    "hostname": "somemachine.in.your.company.com",
	    "processname": "/path/to/your/program.exe",
	    "processid": 3380,
	    "severity": "INFO",
	    "summary": "joe login failed",
	    "category": "authentication",
	    "source": "ldap",
	    "tags": [
	        "ldap",
	        "adminAccess",
            "failure"
	    ],
	    "details": {
	        "user": "joe",
	        "task": "access to admin page /admin_secret_radioactiv",
	        "result": "10 authentication failures in a row"
	    }
	}


.. code-block:: javascript
    {
        "category": "netflow",
        "tags": [
          "netflow",
          "network"
        ],
        "timestamp": "2015-05-04T16:36:52.336527+00:00",
        "summary": "10.247.28.2:60469 --> 2.192.38.177:6824",
        "details": {
          "protocol": 6,
          "destinationmask": 0,
          "sourceipv4address": "10.247.28.2",
          "nexthop": "0.0.0.0",
          "unixnanoseconds": 0,
          "site": "site1",
          "tcpflags": 16,
          "enginetype": 0,
          "engineid": 0,
          "uptime": 96215086,
          "tos": 0,
          "hostname": "fw1.site1.somewhere.net",
          "version": 5,
          "unixseconds": 1430757412,
          "sourceport": 60469,
          "destinationport": 6824,
          "flowsequence": 93808622,
          "octets": 1656,
          "destinationipgeolocation": {
            "city": "Beijing",
            "region_code": "22",
            "area_code": 0,
            "time_zone": "Asia/Harbin",
            "dma_code": 0,
            "metro_code": null,
            "country_code3": "CHN",
            "latitude": 39.9289,
            "postal_code": null,
            "longitude": 116.38830000000002,
            "country_code": "CN",
            "country_name": "China",
            "continent": "AS"
          },
          "samplinginterval": 100,
          "sourceasn": 0,
          "sourceipaddress": "10.247.28.2",
          "count": 29,
          "destinationipaddress": "2.192.38.177",
          "last": 96205073,
          "sourcemask": 21,
          "packets": 4,
          "destinationasn": 0,
          "sitetype": "office",
          "destinationipv4address": "2.192.38.177",
          "first": 96161074
        }
    }



Writing alerts
--------------

Alerts allow you to create notifications based on events stored in elasticsearch.
You would usually try to aggregate and correlate events that are the most severe and on which you have response capability.
Alerts are stored in the `alerts`_ folder.

There are two types of alerts:

* simple alerts that consider events on at a time. For example you may want to get an alert everytime a single LDAP modification is detected.
* aggregation alerts allow you to aggregate events on the field of your choice. For example you may want to alert when more than 3 login attempts failed for the same username.

To narrow the events your alert sees, you need to specify filters. You can either use `pyes`_ to do that or load them from a Kibana dashboard.

You'll find documented examples in the `alerts`_ folder.

Once you've written your alert, you need to configure it in celery to be launched periodically.
If you have a ``AlertBruteforceSsh`` class in a ``alerts/bruteforce_ssh.py`` file for example, in ``alerts/lib/config`` you can configure the task to run every minute::

	ALERTS = {
		'bruteforce_ssh.AlertBruteforceSsh': crontab(minute='*/1'),
	}

.. _alerts: https://github.com/jeffbryner/MozDef/tree/master/alerts
.. _pyes: http://pyes.readthedocs.org/
