Alert Development Guide
=======================


This guide is for someone seeking to write a MozDef alert.


Starting a feature branch
-------------------------

Before you do anything else, start with checking out the MozDef repo and starting a feature branch::

  git clone git@github.com:mozilla/MozDef.git
  cd MozDef
  git checkout -b name_of_alert_you_want_to_create


How to start your alert
-----------------------

Run::

  make new-alert

This will prompt for information and create two things:

- The new alert file
- The new alert test file

You can now edit these files in place, but it is recommended that you run unit-tests on the new alert to make sure it passes before editing (instructions below).


How to run tests on your alert
------------------------------
Requirements:

- Make sure you have the latest version of docker installed.
- Known Issue: docker's overlayfs has a known issue, so you will need to go to Docker => Preferences => Daemon => Advanced and add the following key pair ("storage-driver" : "aufs")

::

  make build-tests
  make run-tests TEST_CASE=tests/alerts/[YOUR ALERT TEST FILE].py

This test should pass and you will have confirmed you have a working environment.

At this point, begin development and periodically run your unit-tests locally with the following commands::

  make build-tests
  make run-tests TEST_CASE=tests/alerts/[YOUR ALERT TEST FILE].py


Background on concepts
----------------------

- Logs - These are individual log line that are emitted from systems, like an Apache log
- Events - These logs parsed into a JSON format, which exist in MozDef and used with the ELK stack
- Alerts - These are effectively either a 1:1 events to alerts (this thing happens and alert) or a M:1 events to alerts (N of these things happen and alert).

When writing alerts, it's important to keep the above concepts in mind.

Each alert tends to have two different blocks of code:

- main - This is where the alert defines the criteria for the types of events it wants to look at
- onAggregation/onEvent - This is where the alert defines what happens when it sees those events, such as post processing of events and making them into a useful summary to emit as an alert.

In both cases, because the alert is simple Python, you will find that getting started writing alerts is pretty easy.  It's important to note that when you iterate on the alert to regularly test to ensure that the alert is still firing.  Should you run into a space where it's not firing, the best way to approach this is to backout the recent change and review the alert and tests to ensure that the expectations are still in sync.


How to get the alert in MozDef?
-------------------------------

The best way to get your alert into MozDef (once it's completed) is to propose a pull request and ask for a review from a MozDef developer.  They will be able to help you get the most out of the alert and help point out pitfalls.  Once the alert is accepted into MozDef master, there is a process by which MozDef installations can make use or 'enable' that alert.  It's best to work with that MozDef instance's maintainer to enable any new alerts.


Example first alert
-------------------
Let's step through creating a simple alert you might want to verify a working deployment.
For this sub-section it is assumed that you have a working MozDef instance which resides in some MozDefDir and is receiving logs.

First move to to your MozDefDir and issue
::

  make new-alert

You will be asked for a string to name a new alert and the associated test. For this example we will use the string "foo"
::

  make new-alert
  Enter your alert name (Example: proxy drop executable): foo
  Creating alerts/foo.py
  Creating tests/alerts/test_foo.py

These will be created as above in the alerts and tests/alerts directories.
There's a lot to the generated code, but a class called  "AlertFoo" is of immediate interest and will define when and how to alert.
Here's the head of the auto generated class.
::

  class AlertFoo(AlertTask):
    def main(self):
        # Create a query to look back the last 20 minutes
        search_query = SearchQuery(minutes=20)

        # Add search terms to our query
        search_query.add_must([
            TermMatch('category', 'helloworld'),
            ExistsMatch('details.sourceipaddress'),
        ])
        ...

In essence this code will tell MozDef to query the collection of logs for messages timestamped within 20 minutes (from time of query execution) and to look for messages which are of category "helloworld" which also have a source IP address.
If you're pumping logs into MozDef odds are you don't have any which will be tagged as "helloworld". You can of course create those logs, but lets assume that you have logs tagged as "syslog" for the moment.
Change the TermMatch line to
::

  TermMatch('category', 'syslog'),

and you will get alerts for syslog labeled messages.
Ideally you should edit your test to match, but it's not strictly necessary.

Scheduling your alert
---------------------
Next we will need to enable the log and to schedule it. At time of writing this is a bit annoying.
Open the file
::

  docker/compose/mozdef_alerts/files/config.py

or simply
::

  alerts/files/config.py

if you are not working from the docker images
and add your new foo alert to the others with a crontab style schedule
::

  ALERTS = {
    'foo.AlertFoo': {'schedule': crontab(minute='*/1')},
    'bruteforce_ssh.AlertBruteforceSsh': {'schedule': crontab(minute='*/1')},
    'unauth_ssh.AlertUnauthSSH': {'schedule': crontab(minute='*/1')},
  }

Restart your MozDef instance and you should begin seeing alerts on the alerts page.

Questions?
----------

This guide is not intended to teach you how to develop in Python, there are good resources below to help you get more experience with Python.  However, should you have questions or run into problems trying to write an alert, we would like to hear from you (in IRC/Slack) so we can:

- help you get what you want to get done
- make it easier for anyone to contribue alerts


Resources
---------

Python for Beginners <https://www.python.org/about/gettingstarted/>
