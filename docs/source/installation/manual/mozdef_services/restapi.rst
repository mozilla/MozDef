RestAPI
*******

The MozDef RestAPI service is an HTTP API that works alongside the Mozdef Web Service.

Copy over systemd file::

  cp /opt/mozdef/envs/mozdef/systemdfiles/web/mozdefrestapi.service /usr/lib/systemd/system/mozdefrestapi.service


Start loginput service::

  systemctl start mozdefrestapi
  systemctl enable mozdefrestapi


Verify service is working::

  curl http://localhost:8081/status


You should see some json returned!
