Overview
========

Why?
----

The inspiration for MozDef comes from the large arsenal of tools available to attackers.
Suites like metasploit, armitage, lair, dradis and others are readily available to help attackers coordinate, share intelligence and finely tune their attacks in real time.
Defenders are usually limited to wikis, ticketing systems and manual tracking databases attached to the end of a Security Information Event Management (SIEM) system.

The Mozilla Defense Platform (MozDef) seeks to automate the security incident handling process and facilitate the real-time activities of incident handlers.

Goals
-----

High level
**********

* Provide a platform for use by defenders to rapidly discover and respond to security incidents.
* Automate interfaces to other systems like bunker, banhammer, mig
* Provide metrics for security events and incidents
* Facilitate real-time collaboration amongst incident handlers
* Facilitate repeatable, predictable processes for incident handling
* Go beyond traditional SIEM systems in automating incident handling, information sharing, workflow, metrics and response automation

Technical
*********

* Replace a SIEM
* Scalable, should be able to handle thousands of events/s, provide fast searching, alerting and correlations and handle interactions between teams of incident handlers.

MozDef aims to provide traditional SIEM functionality including: 

* Accepts events/logs from your systems
* Stores the events/logs
* Facilitate searches
* Facilitate alerting
* Facilitate log management (archiving,restoration)

It is non-traditional in that it:

* Accepts only JSON input
* Provides you open access to your data
* Integrates with a variety of log shippers including  heka, logstash, beaver, nxlog and any shipper that can send JSON to either rabbit-mq or an HTTP endpoint. 
* Provides easy python plugins to manipulate your data in transit
* Provides realtime access to teams of incident responders to allow each other to see their work simultaneously


Architecture
------------
MozDef is based on open source technologies including:

* Nginx (http(s) based log input)
* Rabbit-MQ (message queue)
* UWSGI (supervisory control of python-based workers)
* bottle.py (simple pyhon interface for web request handling)
* Elastic Search (scalable indexing and searching of JSON documents)
* Meteor (responsive framework for Node.js enabling real-time data sharing)
* Mongo DB (scalable data store, tightly integrated to Meteor)
* VERIS from verizon (open source taxonomy of security incident categorizations)
* d3 (javascript library for data driven documents)
* three.js (javascript library for 3d visualizations)

Status
------

MozDef is in early proof of concept phases at Mozilla.

Roadmap
-------
