Installation
============

`For the Mozilla setup, please have a look at the MozDef Mana page.`

The installation process has been tested on CentOS 6 and RHEL 6.

Docker
------

You can quickly install MozDef with an automated build generation using `docker`_.

Dockerfile
***********

After installing `docker`_, use this to build a new image::

  cd docker && sudo make build 

Running the container::

  sudo make run

You're done! Now go to:

 * http://127.0.0.1:3000 < meteor (main web interface)
 * http://127.0.0.1:9090 < kibana
 * http://127.0.0.1:9200 < elasticsearch
 * http://127.0.0.1:9200/\_plugin/marvel < marvel (monitoring for elasticsearch)
 * http://127.0.0.1:8080 < loginput
 * http://127.0.0.1:8081 < rest api

Known issues
*************

* Marvel doesn't display node info: ` Oops! FacetPhaseExecutionException[Facet [fs.total.available_in_bytes]: failed to find mapping for fs.total.available_in_bytes]`

Marvel uses techniques to gather system info that are not compatible with docker.
See https://groups.google.com/forum/#!topic/elasticsearch/dhpxaOuoZWI

Despite this issue, marvel runs fine.

* I don't see any data or dashboards in Kibana

We need to create some sample data, it's in our roadmap ;)

.. _docker: https://www.docker.io/


Elasticsearch nodes
-------------------

This section explains the manual installation process for Elasticsearch nodes (search and storage).

ElasticSearch
*************

Installation instructions are available on `Elasticsearch website`_.
You should prefer packages over archives if one is available for your distribution.

.. _Elasticsearch website: http://www.elasticsearch.org/overview/elkdownloads/

Marvel plugin
*************

`Marvel`_ is a monitoring plugin developed by Elasticsearch (the company).

WARNING: this plugin is NOT open source. At the time of writing, Marvel is free for development but you have to get a license for production.

To install Marvel, on each of your elasticsearch node, from the Elasticsearch home directory::

  bin/plugin -i elasticsearch/marvel/latest
  sudo service elasticsearch restart

You should now be able to access to Marvel at http://any-server-in-cluster:9200/_plugin/marvel

.. _Marvel: http://www.elasticsearch.org/overview/marvel/

Web and Workers nodes
---------------------

This section explains the manual installation process for Web and Workers nodes.

Python
******

We need to install a python2.7 virtualenv::

  sudo yum install make zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel pcre-devel gcc gcc-c++
  cd
  wget http://python.org/ftp/python/2.7.6/Python-2.7.6.tgz
  tar xvzf http://python.org/ftp/python/2.7.6/Python-2.7.6.tgz
  ./configure --prefix=/home/mozdef/python2.7 --enable-shared
  make
  make install

  wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
  export LD_LIBRARY_PATH=/home/netantho/python2.7/lib/
  ./python2.7/bin/python get-pip.py
  ./python2.7/bin/pip install virtualenv
  mkdir ~/envs
  cd ~/envs
  ~/python2.7/bin/virtualenv mozdef
  source mozdef/bin/activate
  pip install -r MozDef/requirements.txt

At this point when you launch python, It should tell you that you're using Python 2.7.6.

Whenever you launch a python script from now on, you should have your mozdef virtualenv actived and your LD_LIBRARY_PATH env variable should include /home/mozdef/python2.7/lib/

RabbitMQ
********

`RabbitMQ`_ is used on workers to have queues of events waiting to be inserted into the Elasticsearch cluster (storage).

To install it, first make sure you enabled `EPEL repos`_. Then you need to install an Erlang environment::

  yum install erlang

You can then install the rabbitmq server::

  rpm --import http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
  yum install rabbitmq-server-3.2.4-1.noarch.rpm

To start rabbitmq at startup::

  chkconfig rabbitmq-server on

.. _RabbitMQ: https://www.rabbitmq.com/
.. _EPEL repos: http://fedoraproject.org/wiki/EPEL/FAQ#howtouse

Meteor
******

`Meteor`_ is a javascript framework used for the realtime aspect of the web interface.

We first need to install `Mongodb`_ since it's the DB used by Meteor.
In /etc/yum.repo.d/mongo, add::

  [mongodb]
  name=MongoDB Repository
  baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64/
  gpgcheck=0
  enabled=1

Then you can install mongodb::

  sudo yum install mongodb

For meteor, in a terminal::

  curl https://install.meteor.com/ | sh

  wget http://nodejs.org/dist/v0.10.26/node-v0.10.26.tar.gz
  tar xvzf node-v0.10.26.tar.gz
  cd node-v0.10.26
  ./configure
  make
  make install

Make sure you have meteorite/mrt::

  npm install -g meteorite

Then from the meteor subdirectory of this git repository run::

  mrt add iron-router
  mrt add accounts-persona

You may want to edit the app/lib/settings.js file to properly point to your elastic search server::

  elasticsearch={
    address:"http://servername:9200/",
    healthurl:"_cluster/health",
    docstatsurl:"_stats/docs"
  }

Then start meteor with::

  meteor

.. _Meteor: https://www.meteor.com/
.. _Mongodb: https://www.mongodb.org/

Nginx
*****

We use `nginx`_ webserver.

You need to install nginx::

  sudo yum install nginx

If you don't have this package in your repos, before installing create `/etc/yum.repos.d/nginx.repo` with the following content::

  [nginx]
  name=nginx repo
  baseurl=http://nginx.org/packages/centos/6/$basearch/
  gpgcheck=0
  enabled=1

.. _nginx: http://nginx.org/

UWSGI
*****

We use `uwsgi`_ to interface python and nginx::

  wget http://projects.unbit.it/downloads/uwsgi-2.0.2.tar.gz
  ~/python2.7/bin/python uwsgiconfig.py --build
  ~/python2.7/bin/python uwsgiconfig.py  --plugin plugins/python core
  cp python_plugin.so ~/envs/mozdef/bin/
  cp uwsgi ~/envs/mozdef/bin/

  cd rest
  # modify uwsgi.ini
  vim uwsgi.ini
  uwsgi --ini uwsgi.ini

  cd ../loginput
  # modify uwsgi.ini
  vim uwsgi.ini
  uwsgi --ini uwsgi.ini

  sudo cp nginx.conf /etc/nginx
  # modify /etc/nginx/nginx.conf
  sudo vim /etc/nginx/nginx.conf
  sudo service nginx restart

.. _uwsgi: http://projects.unbit.it/uwsgi/

Kibana
******

`Kibana`_ is a webapp to visualize and search your Elasticsearch cluster data::

  wget https://download.elasticsearch.org/kibana/kibana/kibana-3.0.0milestone5.tar.gz
  tar xvzf kibana-3.0.0milestone5.tar.gz
  mv kibana-3.0.0milestone5 kibana
  # configure /etc/nginx/nginx.conf to target this folder
  sudo service nginx reload

Import dashboards from `MozDef/kibana/dashboards` into the kibana webUI

.. _Kibana: http://www.elasticsearch.org/overview/kibana

