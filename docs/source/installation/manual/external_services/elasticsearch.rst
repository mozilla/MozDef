ElasticSearch
*************

This section explains the manual installation process for `Elasticsearch`_ nodes (search and storage).
MozDef supports Elasticsearch version 6.8

Create /etc/yum/repos.d/elasticsearch.repo::

  [elasticsearch-6.8]
  name=Elasticsearch repository for 6.8 packages
  baseurl=https://artifacts.elastic.co/packages/6.8/yum
  gpgcheck=1
  gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
  enabled=1
  autorefresh=1
  type=rpm-md

Install elasticsearch::

  yum install elasticsearch

Start Service::

  systemctl start elasticsearch
  systemctl enable elasticsearch

.. _Elasticsearch website: https://www.elastic.co/products/elasticsearch