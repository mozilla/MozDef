Initial Setup
=============

System Setup
************

Create the  user::

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

Setting up a Python 3.6 virtual environment::

  yum install -y epel-release
  yum install -y python36 python36-devel python3-pip libcurl-devel gcc
  pip3 install virtualenv
  su mozdef
  cd /opt/mozdef/envs
  /usr/local/bin/virtualenv -p /bin/python3 /opt/mozdef/envs/python

Install MozDef python requirements::

  su mozdef
  source /opt/mozdef/envs/python/bin/activate
  cd /opt/mozdef/envs/mozdef
  PYCURL_SSL_LIBRARY=nss pip install -r requirements.txt


Setup Syslog
************

Copy over mozdef syslog file::

  cp /opt/mozdef/envs/mozdef/config/50-mozdef-filter.conf /etc/rsyslog.d/50-mozdef-filter.conf

Restart rsyslog::

  systemctl restart rsyslog
