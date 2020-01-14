Bot
***

The MozDef Bot service is a method for sending alerts to either an IRC or slack channel(s).

The source code for this service is broken up into multiple directories, depending on if you want to use Slack or IRC. For this example, we're going to be using the Slack functionality.

Let's edit the configuration file and set our channel and secrets accordingly::

  vim /opt/mozdef/envs/mozdef/bot/slack/mozdefbot.conf


Copy over systemd file::

  cp /opt/mozdef/envs/mozdef/systemdfiles/alert/mozdefbot.service /usr/lib/systemd/system/mozdefbot.service

Start bot service::

  systemctl start mozdefbot
  systemctl enable mozdefbot

Look at logs::

  tail -f /var/log/mozdef/mozdefbot.log
