Alert Actions
*************

The Alert Actions service consists of pluggable modules that perform certain actions if certain alerts are detected. These actions are simply python files, so actions like sending an email or triggering a pagerduty notification are possible.

These actions are stored in `/opt/mozdef/envs/mozdef/alerts/actions/`

Let's edit the configuration file::

  vim /opt/mozdef/envs/mozdef/alerts/lib/config.py


The `ALERT_ACTIONS` list is where we define what alert actions are running. Each entry is simply the filename of the alert action to run (excluding the .py extension). An example::

  ALERT_ACTIONS = [
      'pagerDutyTriggerEvent',
  ]


Copy over systemd file::

  cp /opt/mozdef/envs/mozdef/systemdfiles/alert/mozdefalertactions.service /usr/lib/systemd/system/mozdefalertactions.service


Start alert actions service::

  systemctl start mozdefalertactions
  systemctl enable mozdefalertactions

Look at logs::

  tail -f /var/log/mozdef/alertactions.log
