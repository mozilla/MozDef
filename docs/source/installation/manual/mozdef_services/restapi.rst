RestAPI
*******

The MozDef RestAPI service is an HTTP API that works alongside the Mozdef Web Service.

Copy over systemd file::

  cp /opt/mozdef/envs/mozdef/systemdfiles/web/mozdefrestapi.service /usr/lib/systemd/system/mozdefrestapi.service


Start loginput service::

  systemctl start mozdefrestapi
  systemctl enable mozdefrestapi


This service won't be publicly accessible out of the gate, we'll put an Nginx proxy in front of it to solve that problem!
