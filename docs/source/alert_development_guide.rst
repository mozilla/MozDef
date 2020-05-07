Alert Development Guide
=======================


This guide is for someone seeking to write a MozDef alert


How to start developing your new alert
--------------------------------------

Run::

  make new-alert

This will prompt for information and create two things:

- <The new alert file>
- <The new alert test file>

You can now edit these files in place, but it is recommended that you run unit-tests on the new alert to make sure it passes before editing (instructions below).


How to run tests on your alert
------------------------------
Requirements:

- Make sure you have the latest version of docker installed.
- Known Issues: docker's overlayfs has a known issue with tar files, so you will need to go to Docker => Preferences => Daemon => Advanced and add the following key pair ("storage-driver" : "aufs"). You may also need to allow more than 2GB for docker depending on which containers you run.

::

  make build-tests
  make run-tests TEST_CASE=tests/alerts/[YOUR ALERT TEST FILE].py

This test should pass and you will have confirmed you have a working environment.

At this point, begin development and periodically run your unit-tests locally with the following commands::

  make build-tests
  make run-tests TEST_CASE=tests/alerts/[YOUR ALERT TEST FILE].py


Background on concepts
----------------------

- Logs - These are individual log entries that are typically emitted from systems, like an Apache log.
- Events - The entry point into MozDef, a log parsed into JSON by some log shipper (syslog-ng, nxlog) or a native JSON data source like GuardDuty, CloudTrail, most SaaS systems, etc.
- Alerts - These are either a 1:1 events to alerts (this thing happens and alert) or a M:1 events to alerts (N of these things happen and alert).

Alerts in MozDef are mini python programs. Most of the work is done by the alert library so the portions you will need to code fall into two functions:

- main - This is where the alert defines the criteria for the types of events that will trigger the alert.
- onAggregation/onEvent - This is where the alert defines what happens when it sees those events, such as post processing of events and making them into a useful summary to emit as an alert.

In both cases the alert is simple python, and you have all the facility of python at your disposal including any of the python libraries you might want to add to the project.

It's important to note that when you iterate on the alert to regularly test to ensure that the alert is still firing.  Should you run into a situation where it's not firing, the best way to approach this is to backout the most recent change and review the alert and tests to ensure that the expectations are still in sync.


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

This code tells MozDef to query the collection of events for messages timestamped within 20 minutes from time of query execution which are of category "helloworld" and also have a source IP address.
If you're pumping events into MozDef odds are you don't have any which will be tagged as "helloworld". You can of course create those events, but lets assume that you have events tagged as "syslog" for the moment.
Change the TermMatch line to
::

  TermMatch('category', 'syslog'),

and you will create alerts for events marked with the category of 'syslog'.
Ideally you should edit your test to match, but it's not strictly necessary.

Scheduling your alert
---------------------
Next we will need to enable the alert. Alerts in MozDef are scheduled via the celery task scheduler. The schedule
passed to celery is in the config.py file:

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
  }

The format is `'pythonfilename.classname': {'schedule': crontab(timeunit='*/x')}` and you can use any celery time unit (minute, hour) along with any schedule that makes sense for your environment.
Alerts don't take many resources to execute, typically finishing in sub second times, so it's easiest to start by running them every minute.

How to run the alert in the docker containers
----------------------------------------------
Once you've got your alert passing tests, you'd probably like to send in events in a docker environment to further refine, test, etc.


There are two ways to go about integration testing this with docker:
1) Use 'make run' to rebuild the containers each time you iterate on an alert
2) Use docker-compose with overlays to instantiate a docker environment with a live container you can use to iterate your alert

In general, the 'make run' approach is simpler, but can take 5-10mins each iteration to rebuild the containers (even if cached).

To use the 'make run' approach, you edit your alert. Add it to the docker/compose/mozdef_alerts/files/config.py file for scheduling as discussed above and simply:
::

  make run

This will rebuild any container that needs it, use cache for any that haven't changed and restart mozdef with your alert.



To use a live, iterative environment via docker-compose:
::

  docker-compose -f docker/compose/docker-compose.yml -f docker/compose/dev-alerts.yml -p mozdef up

This will start up all the containers for a mozdef environment and in addition will allow you an adhoc alerts container to work in that loads the /alerts directory as a volume in the container.
To run the alert you are developing you will need to edit the alerts/lib/config.py file as detailed above to schedule your alert. You will also need to edit it to reference the container environment as follows
::

  RABBITMQ = {
      'mqserver': 'rabbitmq',
  ...
  ES = {
    'servers': ['http://elasticsearch:9200']
  }

Once you've reference the containers, you can shell into the alerts container:
::

  docker exec -it mozdef_alerts_1 bash

Next, start celery
::

  celery -A lib.tasks worker --loglevel=info --beat

If you need to send in adhoc events you can usually do it via curl as follows:
::

  curl -v --header "Content-Type: application/json" --request POST --data '{"tags": ["test"],"category": "helloworld","details":{"sourceipaddress":"1.2.3.4"}}' http://loginput:8080/events


How to get the alert in a release of MozDef?
--------------------------------------------

If you'd like your alert included in the release version of Mozdef, the best way is to propose a pull request and ask for a review from a MozDef developer.  They will be able to help you get the most out of the alert and help point out pitfalls.  Once the alert is accepted into MozDef master, there is a process by which MozDef installations can make use or 'enable' that alert.  It's best to work with that MozDef instance's maintainer to enable any new alerts.

Customizing the alert summary
-----------------------------
On the alerts page of the MozDef web UI each alert is given a quick summary and for many alerts it is useful to have contextual information displayed here. Looking at the example foo alert we see
::

  def onAggregation(self, aggreg):
      # aggreg['count']: number of items in the aggregation, ex: number of failed login attempts
      # aggreg['value']: value of the aggregation field, ex: toto@example.com
      # aggreg['events']: list of events in the aggregation
      category = 'My first alert!'
      tags = ['Foo']
      severity = 'NOTICE'
      summary = "Foo alert"

      # Create the alert object based on these properties
      return self.createAlertDict(summary, category, tags, aggreg['events'], severity)

This is where the alert object gets created and returned. In the above code the summary will simply be "Foo Alert", but say we want to know how many log entries were collected in the alert? The aggreg object is here to help.
::

  summary = "Foo alert " +  aggreg['count']

Gives us an alert with a count. Similarly
::

  summary = "Foo alert " +  aggreg['value']

Will append the aggregation field to the summary text. The final list aggreg['events'] contains the full log entries of all logs collected and is in general the most useful. Suppose we want one string if the tag 'foo' exists on these logs and another otherwise
::

  if 'foo' in aggreg['events'][0]['_source']['tags']:
    summary = "Foo alert"
  else:
    summary = "Bar alert"

All source log data is held within the ['_source'] and [0] represents the first log found. Beware that no specific ordering of the logs is guaranteed and so [0] may be first, last, or otherwise chronologically.

Questions?
----------

Feel free to file a github issue in this repository if you find yourself with a question not answered here. Likely the answer will help someone else and will help us improve the docs.


Resources
---------

Python for Beginners <https://www.python.org/about/gettingstarted/>
