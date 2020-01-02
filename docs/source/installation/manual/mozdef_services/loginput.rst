Loginput
********

The MozDef Loginput service is an HTTP API to send events to MozDef by external sources.

Copy over systemd file::

  cp /opt/mozdef/envs/mozdef/systemdfiles/consumer/mozdefloginput.service /usr/lib/systemd/system/mozdefloginput.service


Start loginput service::

  systemctl start mozdefloginput
  systemctl enable mozdefloginput


This service won't be publicly accessible out of the gate, we'll put an Nginx proxy in front of it to solve that problem!
