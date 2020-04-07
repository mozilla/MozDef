Loginput
********

The MozDef Loginput service is an HTTP API to send events to MozDef by external sources.

Copy over systemd file::

  cp /opt/mozdef/envs/mozdef/systemdfiles/consumer/mozdefloginput.service /usr/lib/systemd/system/mozdefloginput.service


Start loginput service::

  systemctl start mozdefloginput
  systemctl enable mozdefloginput


Verify service is working::

  curl http://localhost:8080/status


You should see some json returned!
