Alert Development
============

This guide is for someone seeking to write a MozDef alert plugin.


Starting a feature branch
-------------

Before you do anything else, start with checking out the MozDef repo and starting a feature branch.

`git clone git@github.com:mozilla/MozDef.git`
`cd MozDef`
`git checkout -b name_of_alert_you_want_to_create`


Where do alerts live?
-------------

Alerts and their associated tests live in ./alerts and ./tests/alerts.  If you plan to write an alert, you will need produce a minumum of those files.  You can use other alerts and associated tests as a means to copy and paste and iterate.  It's also helpful if you pick an alert that is similar in category as a base.  For instance, if you would like to write a proxy alert, use the patterns that exist in existing proxy alerts as guidance, though they will likely require modification.

Things you will likely need to change after copying your alert to make sure you have a functional alert base..

- The names of the alert file and the test file (should be ./alerts/alert_name.py and ./tests/alerts/test_alert_name.py respectively)
- The class name in the alert and in the alert test files
- The alert_filename variable in the test file

Once you've made these changes (without any others), you should be able to perform a unit-test run against your new alert to know that it functionally works and you're starting on good footing.


How to get up for test-runs?
-------------

Make sure you have the latest version of docker installed.

Known Issue: docker's overlayfs has a known issue, so you will need to go to Docker => Preferences => Daemon => Advanced and add the following key pair ("storage-driver" : "aufs")

To get your local development environment setup for running tests, you need to run the following...

`make build-test`

This will build all the essential docker containers, then you can run this..

`make run-test ./tests/alerts/test_proxy_drop_executable.py`

This test should pass and you will have confirmed you have a working environment.

At this point, you can run tests on your copy to ensure it too is a working base to begin development.


Background on concepts
-------------

Logs - These are individual log line that are emitted from systems, like an Apache log
Events - These logs parsed into a JSON format, which exist in MozDef and used with the ELK stack
Alerts - These are effectively either a 1:1 events to alerts (this thing happens and alert) or a M:1 events to alerts (N of these things happen and alert).

When writing alerts, it's important to keep the above concepts in mind.

Each alert tends to have two different blocks of code:

main - This is where the alert defines the criteria for the types of events it wants to look at
onAggregation/onEvent - This is where the alert defines what happens when it sees those events, such as post processing of events and making them into a useful summary to emit as an alert. 

In both cases, because the alert is simple Python, you will find that getting started writing alerts is pretty easy.  It's important to note that when you change the alert from the base you copied to regularly test to ensure that the alert is still firing.  Should you run into a space where it's not firing, the best way to approach this is to backout the recent change and review the tests to ensure that the expectations are still the same.

How to get the alert in MozDef?
-------------

The best way to get your alert (once it's completed) into MozDef is to propose a pull request and ask for a review from a MozDef developer.  They will be able to help you get the most out of the alert and help point out pitfalls.  Once the alert is accepted into MozDef master, there is a process by which MozDef installations can make use or 'enable' that alert.  It's best to work with that MozDef instance's maintainer to enable the alerts.


Questions?
-------------

This guide is not intended to teach you how to develop in Python, there are some good resources below we would point you to to get more experience there.  However, should you have questions or run into problems trying to write an alert, we would like to hear from you (in IRC/Slack) so we can (1) help you get what you want to get done and (2) make it easier in the future for anyone to contribue alert logic to MozDef.




