MozDef Services
===============

MozDef services can be broken up into 3 different groups (Alert, Ingest, Web). Each group of services should be run on the same machine, with all of the Ingest services able to run on N number of machines, allowing for a more distrubuted environment.

.. note:: It's recommended in a distributed environment, to have only 1 Alert Service node, 1 Web Service node, and N Ingest Service nodes.

+------------------+------------------------+------------------------------------------+
| MozDef Service   |     Service Type       |      Required Service(s)                 |
+==================+========================+==========================================+
| Alerts           | Alert                  | Elasticsearch, RabbitMQ, MozdefRestAPI   |
+------------------+------------------------+------------------------------------------+
| Alert Actions    | Alert                  | RabbitMQ                                 |
+------------------+------------------------+------------------------------------------+
| Bot              | Alert                  | RabbitMQ                                 |
+------------------+------------------------+------------------------------------------+
| Loginput         | Ingest                 | RabbitMQ, Nginx                          |
+------------------+------------------------+------------------------------------------+
| MQ Workers       | Ingest                 | Elasticsearch, RabbitMQ                  |
+------------------+------------------------+------------------------------------------+
| RestAPI          | Web                    | Elasticsearch, Mongodb, Nginx            |
+------------------+------------------------+------------------------------------------+
| Meteor           | Web                    | Mongodb, MozdefRestAPI, Nginx            |
+------------------+------------------------+------------------------------------------+
| Kibana           | Web                    | Elasticsearch, Nginx                     |
+------------------+------------------------+------------------------------------------+

.. include:: mozdef_services/restapi.rst
.. include:: mozdef_services/alerts.rst
.. include:: mozdef_services/alertactions.rst
.. include:: mozdef_services/bot.rst
.. include:: mozdef_services/cron.rst
.. include:: mozdef_services/loginput.rst
.. include:: mozdef_services/mq_workers.rst
.. include:: mozdef_services/web.rst
