Web Interface
=============

MozDef uses the `Meteor framework`_ for the web interface and bottle.py for the REST API.
For authentication, MozDef supports local account creation.
Meteor (the underlying UI framework) supports `many authentication options`_ including google, github, twitter, facebook, oath, native accounts, etc.

.. _Meteor framework: https://www.meteor.com/
.. _many authentication options: https://docs.meteor.com/#accounts_api

Events visualizations
*********************

Since the backend of MozDef is Elastic Search, you get all the goodness of Kibana with little configuration.
The MozDef UI is focused on incident handling and adding security-specific visualizations of SIEM data to help you weed through the noise.
