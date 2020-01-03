MongoDB
*******

`Mongodb`_ is the backend database used by Meteor (the web UI).

.. note:: It's preferred to run this service on the same host that the Web UI will be running on, so you don't need to expose this service externally.


Create yum repo file::

  vim /etc/yum.repos.d/mongodb.repo

With the following contents::

  [mongodb-org-3.4]
  name=MongoDB Repository
  baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.4/x86_64/
  gpgcheck=1
  enabled=1
  gpgkey=https://www.mongodb.org/static/pgp/server-3.4.asc

Then you can install mongodb::

  yum install -y mongodb-org

Overwrite config file::

  cp /opt/mozdef/envs/mozdef/config/mongod.conf /etc/mongod.conf


Start Service::

  systemctl start mongod
  systemctl enable mongod

.. _Mongodb: https://www.mongodb.com/