Alerts
******

The alerts service searches Elasticsearch for specific terms (defined in specific alerts), and will create an Alert document if any of the alerts found events.

.. note:: The alerts service depends on Elasticsearch, RabbitMQ, AND the MozdefRestAPI.


Let's edit the configuration file::

  vim /opt/mozdef/envs/mozdef/alerts/lib/config.py


The `ALERTS` dictionary is where we define what alerts are running, and with what schedule they run on. The dictionary `key` consists of 2 fields, the alert filename (excluding the .py extension), and the alert classname. The dictionary `value` is a dictionary containing the schedule. An example::

  ALERTS = {
      'bruteforce_ssh.AlertBruteforceSsh': {'schedule': crontab(minute='*/1')},
      'get_watchlist.AlertWatchList': {'schedule': crontab(minute='*/1')},
  }


Copy over systemd file::

  cp /opt/mozdef/envs/mozdef/systemdfiles/alert/mozdefalerts.service /usr/lib/systemd/system/mozdefalerts.service


Start alerts service::

  systemctl start mozdefalerts
  systemctl enable mozdefalerts

Look at logs::

  tail -f /var/log/mozdef/supervisord/alert_errors.log
