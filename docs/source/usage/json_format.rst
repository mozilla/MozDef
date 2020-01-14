JSON format
===========

This section describes the structure JSON objects to be sent to MozDef.
Using this standard ensures developers, admins, etc are configuring their application or system to be easily integrated into MozDef.

Background
**********

Mozilla used CEF as a logging standard for compatibility with Arcsight and for standardization across systems. While CEF is an admirable standard, MozDef prefers JSON logging for the following reasons:

* Every development language can create a JSON structure.
* JSON is easily parsed by computers/programs which are the primary consumer of logs.
* CEF is primarily used by Arcsight and rarely seen outside that platform and doesn't offer the extensibility of JSON.
* A wide variety of log shippers (heka, logstash, fluentd, nxlog, beaver) are readily available to meet almost any need to transport logs as JSON.
* JSON is already the standard for cloud platforms like amazon's cloudtrail logging.

Description
***********

As there is no common RFC-style standard for json logs, we prefer the following structure adapted from a combination of the graylog GELF and logstash specifications.

Note all fields are lowercase to avoid one program sending sourceIP, another sending sourceIp, another sending SourceIPAddress, etc.
Since the backend for MozDef is elasticsearch and fields are case-sensitive this will allow for easy compatibility and reduce potential confusion for those attempting to use the data.
MozDef will perform some translation of fields to a common schema but this is intended to allow the use of heka, nxlog, beaver and retain compatible logs.

Mandatory Fields
****************

+-----------------+-------------------------------------+-----------------------------------+
|    Field        |             Purpose                 |            Sample Value           |
+=================+=====================================+===================================+
| category        | General category/type of event      | authentication, authorization,    |
|                 | matching the 'what should I log'    | account creation, shutdown,       |
|                 | section below                       | atartup, account deletion,        |
|                 |                                     | account unlock, zeek              |
|                 |                                     |                                   |
+-----------------+-------------------------------------+-----------------------------------+
| details         | Additional, event-specific fields   | <see below>                       |
|                 | that you would like included with   |                                   |
|                 | the event. Please completely spell  |                                   |
|                 | out a field rather an abbreviate:   |                                   |
|                 | i.e. sourceipaddress instead of     |                                   |
|                 | srcip.                              |                                   |
+-----------------+-------------------------------------+-----------------------------------+
| hostname        | The fully qualified domain name of  | server1.example.com               |
|                 | the host sending the message        |                                   |
+-----------------+-------------------------------------+-----------------------------------+
| processid       | The PID of the process sending the  | 1234                              |
|                 | log                                 |                                   |
+-----------------+-------------------------------------+-----------------------------------+
|processname      | The name of the process sending the | myprogram.py                      |
|                 | log                                 |                                   |
+-----------------+-------------------------------------+-----------------------------------+
| severity        | RFC5424 severity level of the event | INFO                              |
|                 | in all caps: DEBUG, INFO, NOTICE,   |                                   |
|                 | WARNING, ERROR, CRITICAL, ALERT,    |                                   |
|                 | EMERGENCY                           |                                   |
+-----------------+-------------------------------------+-----------------------------------+
| source          | Source of the event (file name,     | /var/log/syslog/2014.01.02.log    |
|                 | system name, component name)        |                                   |
+-----------------+-------------------------------------+-----------------------------------+
| summary         | Short human-readable version of the | john login attempts over          |
|                 | event suitable for IRC, SMS, etc.   | threshold, account locked         |
+-----------------+-------------------------------------+-----------------------------------+
| tags            | An array or list of any tags you    | vpn, audit                        |
|                 | would like applied to the event     |                                   |
|                 |                                     | nsm,zeek,intel                    |
+-----------------+-------------------------------------+-----------------------------------+
| timestamp       | Full date plus time timestamp of    | 2014-01-30T19:24:43+06:00         |
|                 | the event in ISO format including   |                                   |
|                 | the timezone offset                 |                                   |
+-----------------+-------------------------------------+-----------------------------------+
|utctimestamp     | Full UTC date plus time timestamp of| 2014-01-30T13:24:43+00:00         |
|                 | the event in ISO format including   |                                   |
|                 | the timezone offset                 |                                   |
+-----------------+-------------------------------------+-----------------------------------+
|receivedtimestamp| Full UTC date plus time timestamp in| 2014-01-30T13:24:43+00:00         |
|                 | ISO format when mozdef parses the   |                                   |
|                 | event. This is set by mozdef upon   |                                   |
|                 | receipt of the event                |                                   |
+-----------------+-------------------------------------+-----------------------------------+

Details substructure (mandatory if such data is sent, otherwise optional)
*************************************************************************

+----------------------+--------------------------+---------------------------------+
|        Field         |         Purpose          |          Sample Value           |
+======================+==========================+=================================+
| destinationipaddress | Destination IP of a      | 8.8.8.8                         |
|                      | network flow             |                                 |
+----------------------+--------------------------+---------------------------------+
| destinationport      | Destination port of a    |  80                             |
|                      | network flow             |                                 |
+----------------------+--------------------------+---------------------------------+
| sourceipaddress      | Source IP of a network   | 8.8.8.8                         |
|                      | flow                     |                                 |
+----------------------+--------------------------+---------------------------------+
| sourceport           | Source port of a network | 42297                           |
|                      | flow                     |                                 |
+----------------------+--------------------------+---------------------------------+
| sourceuri            | Source URI such as a     | https://www.mozilla.org/        |
|                      | referer                  |                                 |
+----------------------+--------------------------+---------------------------------+
| destinationuri       | Destination URI as in    | https://www.mozilla.org/        |
|                      | "wget this URI"          |                                 |
+----------------------+--------------------------+---------------------------------+
| error                | Action resulted in an    | true/false                      |
|                      | error or failure         |                                 |
+----------------------+--------------------------+---------------------------------+
| success              | Transaction failed/      | true/false                      |
|                      | or succeeded             |                                 |
+----------------------+--------------------------+---------------------------------+
| username             | Username, email, login,  | kang@mozilla.com                |
|                      | etc.                     |                                 |
+----------------------+--------------------------+---------------------------------+
| useragent            | Program agent string     | curl/1.76 (Windows; 5.1)        |
|                      |                          |                                 |
+----------------------+--------------------------+---------------------------------+

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
            "username": "joe",
            "task": "access to admin page /admin_secret_radioactiv",
            "result": "10 authentication failures in a row",
            "success": false
        }
    }
