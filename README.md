[![Build Status](https://travis-ci.org/mozilla/MozDef.svg?branch=master)](https://travis-ci.org/mozilla/MozDef)
[![Documentation Status](https://readthedocs.org/projects/mozdef/badge/?version=latest)](http://mozdef.readthedocs.io/en/latest/?badge=latest)

# MozDef: The Mozilla Defense Platform

## Why?

The inspiration for MozDef comes from the large arsenal of tools available to attackers. Suites like metasploit, armitage, lair, dradis and others are readily available to help attackers coordinate, share intelligence and finely tune their attacks in real time. Defenders are usually limited to wikis, ticketing systems and manual tracking databases attached to the end of a Security Information Event Management (SIEM) system.

The Mozilla Defense Platform (MozDef) seeks to automate the security incident handling process and facilitate the real-time activities of incident handlers.

## Goals:

* Provide a platform for use by defenders to rapidly discover and respond to security incidents.
* Automate interfaces to other systems like bunker, cymon, mig
* Provide metrics for security events and incidents
* Facilitate real-time collaboration amongst incident handlers
* Facilitate repeatable, predictable processes for incident handling
* Go beyond traditional SIEM systems in automating incident handling, information sharing, workflow, metrics and response automation

## Status:

MozDef is in production at Mozilla where we are using it to process over 300 million events per day.

## Give MozDef a Try in AWS:

[![Launch MozDef](docs/source/images/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=mozdef-for-aws&templateURL=https://s3-us-west-2.amazonaws.com/public.us-west-2.infosec.mozilla.org/mozdef/cf/mozdef-parent.yml)

## Documentation:

http://mozdef.readthedocs.org/en/latest/
