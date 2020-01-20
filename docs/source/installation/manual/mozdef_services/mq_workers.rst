MQ Workers
**********

MQ Workers are the main service to pull events into MozDef. These workers can pull from a queue from RabbitMQ, Cloudtrail, Amazon SQS, Amazon SNS and Papertrail.

The MQ worker files are stored in `/opt/mozdef/envs/mozdef/mq/`.

For this example, we're going to focus on configuring and running the `eventtask` worker. This specific workers pull from a RabbitMQ queue, which will be populated by the MozDef Loginput service.

Each MQ worker service has the following associated files:

1. A .ini file used to control certain properties of the worker service (number of processes, logging directory, etc).
Modify eventtask ini file::

  vim /opt/mozdef/envs/mozdef/mq/eventtask.ini

.. note:: The mules key is used to determine how many "processes" the worker service will run. Depending on the amount of incoming messages, you may need to duplicate this line (thus adding more processes to run).


2. A .conf file used to store credentials and other configuration options for the worker process.
Modify eventtask conf file::

  vim /opt/mozdef/envs/mozdef/mq/esworker_eventtask.conf


3. A systemd file used to start/stop/enable the specific MQ worker.
Copy systemd file into place::

  cp /opt/mozdef/envs/mozdef/systemdfiles/consumer/mworker-eventtask.service /usr/lib/systemd/system/mworker-eventtask.service

Start worker::

  systemctl start mworker-eventtask
  systemctl enable mworker-eventtask
