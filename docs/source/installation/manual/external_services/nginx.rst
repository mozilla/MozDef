Nginx
*****

Nginx is used as a proxy to forward requests to the loginput service.

If Nginx is not installed already (as it's used to proxy other MozDef web services), let's install it::

  yum install -y nginx

Copy mozdef nginx conf::

  cp /opt/mozdef/envs/mozdef/config/nginx.conf /etc/nginx/nginx.conf


Ensure nginx is started and running::

  systemctl start nginx
  systemctl enable nginx
