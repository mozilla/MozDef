Initial Setup
=============

System Setup
************

Create the user::

  adduser mozdef -d /opt/mozdef
  mkdir /opt/mozdef/envs
  chown -R mozdef:mozdef /opt/mozdef

Clone repository::

  yum install -y git
  su mozdef
  cd ~/
  git clone https://github.com/mozilla/MozDef.git /opt/mozdef/envs/mozdef


Python Setup
************

Setting up a Python 3.6 virtual environment (as root)::

  yum install -y epel-release
  yum install -y python36 python36-devel python3-pip libcurl-devel gcc
  pip3 install virtualenv
  su mozdef
  cd /opt/mozdef/envs
  /usr/local/bin/virtualenv -p /bin/python3 /opt/mozdef/envs/python

Install MozDef python requirements (as mozdef user)::

  source /opt/mozdef/envs/python/bin/activate
  cd /opt/mozdef/envs/mozdef
  PYCURL_SSL_LIBRARY=nss pip install -r requirements.txt
  mkdir /opt/mozdef/envs/mozdef/data


Syslog Setup
************

Copy over mozdef syslog file (as root)::

  cp /opt/mozdef/envs/mozdef/config/50-mozdef-filter.conf /etc/rsyslog.d/50-mozdef-filter.conf


Ensure log directory is created::

  mkdir -p /var/log/mozdef/supervisord
  chown -R mozdef:mozdef /var/log/mozdef


Restart rsyslog::

  systemctl restart rsyslog

