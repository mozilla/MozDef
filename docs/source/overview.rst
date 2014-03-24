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


Architecture
------------
MozDef is based on open source technologies including:
1) Nginx (http(s) based log input)
2) Rabbit-MQ (message queue)
3) UWSGI (supervisory control of python-based workers)
4) Elastic Search (scalable indexing and searching of JSON documents)
5) Meteor (responsive framework for Node.js enabling real-time data sharing)
6) Mongo DB (scalable data store, tightly integrated to Meteor)

Status
------

MozDef is in early proof of concept phases at Mozilla.

Roadmap
-------
