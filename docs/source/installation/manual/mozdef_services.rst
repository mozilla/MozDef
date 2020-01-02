MozDef Services
---------------

MozDef services can be broken up into 3 different groups (Alert, Ingest, Web). Each group of services should be run on the same machine, with all of the Ingest services able to run on N number of machines, allowing for a more distrubuted environment.

+------------------+------------------------+------------------------------------------+
| MozDef Service   |         Group          |      External Service                    |
+==================+========================+==========================================+
| Alerts           | Alert Services         | Elasticsearch, RabbitMQ, MozdefRestAPI   |
+------------------+------------------------+------------------------------------------+
| Alert Actions    | Alert Services         | RabbitMQ                                 |
+------------------+------------------------+------------------------------------------+
| Bot              | Alert Services         | RabbitMQ                                 |
+------------------+------------------------+------------------------------------------+
| Loginput         | Ingest Services        | RabbitMQ                                 |
+------------------+------------------------+------------------------------------------+
| MQ Workers       | Ingest Services        | Elasticsearch, RabbitMQ                  |
+------------------+------------------------+------------------------------------------+
| Meteor           | Web Services           | Mongodb                                  |
+------------------+------------------------+------------------------------------------+
| RestAPI          | Web Services           | Elasticsearch, Mongodb                   |
+------------------+------------------------+------------------------------------------+
| Kibana           | Web Services           | Elasticsearch                            |
+------------------+------------------------+------------------------------------------+

.. toctree::
    :maxdepth: 2

    mozdef_services/initial_setup
    mozdef_services/web
    mozdef_services/restapi
    mozdef_services/kibana
    mozdef_services/alerts
    mozdef_services/alertactions
    mozdef_services/bot
    mozdef_services/cron
    mozdef_services/loginput
    mozdef_services/mq_workers
    mozdef_services/nginx
