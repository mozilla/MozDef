Kibana
******

`Kibana`_ is a webapp to visualize and search your Elasticsearch cluster data.

Import public signing key of yum repo::

  rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

Create yum repo file::

  vim /etc/yum.repos.d/kibana.repo

With the following contents::

  [kibana-6.x]
  name=Kibana repository for 6.x packages
  baseurl=https://artifacts.elastic.co/packages/6.x/yum
  gpgcheck=1
  gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
  enabled=1
  autorefresh=1
  type=rpm-md

Install kibana::

  yum install -y kibana

Kibana should work just fine out of the box, but we should take a look at what settings are available::

  cat /etc/kibana/kibana.yml

Some of the settings you'll want to configure are:

* server.name (your server's hostname)
* elasticsearch.url (the url to your elasticsearch instance and port)
* logging.dest ( /path/to/kibana.log so you can easily troubleshoot any issues)

Then you can start the service::

  systemctl start kibana
  systemctl enable kibana


Now that Kibana and Elasticsearch are setup, we can populate the MozDef indices and Kibana settings::

  su mozdef
  source /opt/mozdef/envs/python/bin/activate
  cd /opt/mozdef/envs/mozdef/scripts/setup
  python initial_setup.py http://localhost:9200 http://localhost:5601


.. _Kibana: https://www.elastic.co/products/kibana
