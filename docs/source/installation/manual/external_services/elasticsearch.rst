Elasticsearch
*************

`Elasticsearch`_ is the main data storage of MozDef. It's used to store alerts and event documents, which can then be searched through in a fast and efficient manner. Each day's events is stored in a separate index (events-20190124 for example),

.. note:: MozDef currently only supports Elasticsearch version 6.8

Elasticsearch requires java, so let's install it::

  yum install -y java-1.8.0-openjdk

Import public signing key of yum repo::

  rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch

Create yum repo file::

  vim /etc/yum.repos.d/elasticsearch.repo

With the following contents::

  [elasticsearch-6.x]
  name=Elasticsearch repository for 6.x packages
  baseurl=https://artifacts.elastic.co/packages/6.x/yum
  gpgcheck=1
  gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
  enabled=1
  autorefresh=1
  type=rpm-md

Install elasticsearch::

  yum install -y elasticsearch

Start Service::

  systemctl start elasticsearch
  systemctl enable elasticsearch

It may take a few seconds for Elasticsearch to start up, but we can look at the log file to verify when it's ready::

  tail -f /var/log/elasticsearch/elasticsearch.log

Once the services seems to have finished starting up, we can verify using curl::

  curl http://localhost:9200

You should see some information in JSON about the Elasticsearch endpoint (version, build date, etc). This means Elasticsearch is all setup, and ready to go!

.. _Elasticsearch: https://www.elastic.co/products/elasticsearch
