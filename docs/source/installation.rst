Installation
============

The installation process has been tested on CentOS 7.

Build and run MozDef
--------------------

You can quickly install MozDef with an automated build generation using `docker`::

  make build
  make run

You're done! Now go to:

 * http://localhost < meteor (main web interface)
 * http://localhost:9090/app/kibana < kibana
 * http://localhost:9200 < elasticsearch
 * http://localhost:8080 < loginput
 * http://localhost:8081 < rest api


.. _docker: https://www.docker.io/
.. note:: The build system has changed
   `make` targets for `multiple-*` and `single-*` have been replaced by the above commands (`make run`, etc.)
   Just type `make` to get a list of available targets.

Run tests
---------

Simply run::

  make test


Note, if you end up with a clobbered ES index, or anything like that which might end up in failing tests, you can clean
the environment with::

  make clean

Then run the tests again.


Manual Installation for Yum or Apt based distros
----------------------------------------------------

Summary
*******
This section explains the manual installation process for the MozDef system::

  git clone https://github.com/mozilla/MozDef.git mozdef

Web and Workers nodes
---------------------

This section explains the manual installation process for Web and Workers nodes.

Python
******

Create a mozdef user::

  adduser mozdef -d /opt/mozdef
  cp /etc/skel/.bash* /opt/mozdef/
  cd /opt/mozdef
  chown mozdef: .bash*
  chown -R mozdef: *

We need to install a python2.7 virtualenv.

On Yum-based systems::

  sudo yum install make zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel pcre-devel gcc gcc-c++ mysql-devel

On APT-based systems::

  sudo apt-get install make zlib1g-dev libbz2-dev libssl-dev libncurses5-dev libsqlite3-dev libreadline-dev tk-dev libpcre3-dev libpcre++-dev build-essential g++ libmysqlclient-dev

Then::

  sudo -i -u mozdef -g mozdef
  mkdir /opt/mozdef/python2.7
  wget https://www.python.org/ftp/python/2.7.11/Python-2.7.11.tgz
  tar xvzf Python-2.7.11.tgz
  cd Python-2.7.11
  ./configure --prefix=/opt/mozdef/python2.7 --enable-shared LDFLAGS="-Wl,--rpath=/opt/mozdef/python2.7/lib"
  make
  make install

  cd /opt/mozdef

  wget https://bootstrap.pypa.io/get-pip.py
  export LD_LIBRARY_PATH=/opt/mozdef/python2.7/lib/
  ./python2.7/bin/python get-pip.py
  ./python2.7/bin/pip install virtualenv
  mkdir ~/envs
  cd ~/envs
  ~/python2.7/bin/virtualenv python
  source python/bin/activate
  pip install -r ../requirements.txt

Copy the following into a file called .bash_profile for the mozdef user within /opt/mozdef:

  [mozdef@server ~]$ vim /opt/mozdef/.bash_profile

  # Add the following to the file before "export PATH":

  PATH=$PATH:$HOME/.meteor

  export PATH

At this point when you launch python from within your virtual environment, It should tell you that you're using Python 2.7.11.

Whenever you launch a python script from now on, you should have your mozdef virtualenv active and your LD_LIBRARY_PATH env variable should include /opt/mozdef/python2.7/lib/ automatically.

RabbitMQ
********

`RabbitMQ`_ is used on workers to have queues of events waiting to be inserted into the Elasticsearch cluster (storage).

RabbitMQ does provide a zero-dependency RPM that you can find for RedHat/CentOS here::
https://github.com/rabbitmq/erlang-rpm

For Debian/Ubuntu based distros you would need to install erlang separately.

To install it, first make sure you enabled `EPEL repos`_. Then you need to install an Erlang environment.

If you prefer to install all the dependencies on a Red Hat based system you can do the following::
On Yum-based systems::

  sudo yum install erlang

You can then install the rabbitmq server::

  sudo rpm --import https://www.rabbitmq.com/rabbitmq-signing-key-public.asc
  sudo yum install rabbitmq-server

To start rabbitmq at startup::

  systemctl enable rabbitmq-server

On APT-based systems ::

  sudo apt-get install rabbitmq-server
  sudo invoke-rc.d rabbitmq-server start

We do advise using rabbitmq and erlang's latest versions if you plan on using TLS protected connections with Rabbitmq.
A simple way of doing this would be to use Bintray's repo located at: https://www.rabbitmq.com/install-rpm.html#bintray
to download both the latest versions of rabbitmq and erlang.

.. _RabbitMQ: https://www.rabbitmq.com/
.. _EPEL repos: http://fedoraproject.org/wiki/EPEL/FAQ#howtouse

Meteor
******

`Meteor`_ is a javascript framework used for the realtime aspect of the web interface.

We first need to install `Mongodb`_ since it's the DB used by Meteor.

On Yum-based systems:

In /etc/yum.repos.d/mongo.repo, add::

  [mongodb-org-3.4]
  name=MongoDB Repository
  baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.4/x86_64/
  gpgcheck=1
  enabled=1
  gpgkey=https://www.mongodb.org/static/pgp/server-3.4.asc

Then you can install mongodb::

  sudo yum install mongodb-org

On APT-based systems::

  sudo apt-get install mongodb-server

We have a mongod.conf in the config directory prepared for you. To use it simply move it in to /etc::

  cp /opt/mozdef/config/mongod.conf /etc/

For meteor installation follow these steps::

  sudo -i -u mozdef -g mozdef
  curl https://install.meteor.com/?release=1.8 | sh

For node you can exit from the mozdef user::

  wget https://nodejs.org/dist/v8.12.0/node-v8.12.0.tar.gz
  tar xvzf node-v8.12.0.tar.gz
  cd node-v8.12.0
  ./configure
  make
  sudo make install

Then from the meteor subdirectory of this git repository (/opt/mozdef/meteor) run as the mozdef user with venv activated::

  sudo -i -u mozdef -g mozdef
  source envs/python/bin/activate
  meteor add iron-router

If you wish to use meteor as the authentication handler you'll also need to install the Accounts-Password pkg::

  meteor add accounts-password

You may want to edit the /meteor/imports/settings.js file to properly configure the URLs and Authentication
The default setting will use Meteor Accounts, but you can just as easily install an external provider like Github, Google, Facebook or your own OIDC::

  mozdef = {
    ...
    authenticationType: "meteor-password",
    ...
  }

or for an OIDC implementation that passes a header to the nginx reverse proxy (for example using OpenResty with Lua and Auth0)::

  mozdef = {
    ...
    authenticationType: "OIDC",
    ...
  }

Then start meteor with::

  meteor

.. _Meteor: https://guide.meteor.com/
.. _Mongodb: https://www.mongodb.org/
.. _meteor-accounts: https://guide.meteor.com/accounts.html


Node
******

Alternatively you can run the meteor UI in 'deployment' mode using a native node installation.

First install node::

    yum install bzip2 gcc gcc-c++ sqlite sqlite-devel
    wget https://nodejs.org/dist/v8.12.0/node-v8.12.0.tar.gz
    tar xvzf node-v8.12.0.tar.gz
    cd node-v8.12.0
    ./configure
    make
    sudo make install

Then bundle the meteor portion of mozdef to deploy on another server::

  cd <your meteor mozdef directory>
  meteor bundle mozdef.tgz

You can then deploy the meteor UI for mozdef as necessary::

  scp mozdef.tgz to your target host
  tar -xvzf mozdef.tgz

This will create a 'bundle' directory with the entire UI code below that directory.

If you didn't update the settings.js before bundling the meteor installation, you will need to update the settings.js file to match your servername/port::

  vim bundle/programs/server/app/imports/settings.js

If your development OS is different than your production OS you will also need to update
the fibers node module::

  cd bundle/programs/server/node_modules
  rm -rf fibers
  sudo npm install fibers@1.0.1

Or you can bundle the meteor portion of mozdef to deploy on into a different directory.
In this example we place it in /opt/mozdef/envs/meteor/mozdef::

  #!/bin/bash

  if [ -d /opt/mozdef/meteor ]
  then
      cd /opt/mozdef/meteor
      source /opt/mozdef/envs/python/bin/activate
      mkdir -p /opt/mozdef/envs/meteor/mozdef

      meteor npm install
      meteor build --server localhost:3002 --directory /opt/mozdef/envs/meteor/mozdef/
      cp -r node_modules /opt/mozdef/envs/meteor/mozdef/node_modules
  else
    echo "Meteor does not exist on this host."
    exit 0
  fi

There are systemd unit files available in the systemd directory of the public repo you can use to start mongo, meteor (mozdefweb), and the restapi (mozdefrestapi).
These systemd files are pointing to the bundled alternative directory we just mentioned.

If you aren't using systemd, or didn't bundle to the alternative directory, then run the mozdef UI via node manually::

  export MONGO_URL=mongodb://mongoservername:3002/meteor
  export ROOT_URL=http://meteorUIservername/
  export PORT=443
  node bundle/main.js


Nginx
*****

We use `nginx`_ webserver.

You need to install nginx::

  sudo yum install nginx

On apt-get based system::

  sudo apt-get nginx

If you don't have this package in your repos, before installing create `/etc/yum.repos.d/nginx.repo` with the following content::

 [nginx]
 name=nginx repo
 baseurl=http://nginx.org/packages/centos/7/$basearch/
 gpgcheck=0
 enabled=1

.. _nginx: http://nginx.org/

UWSGI
*****

We use `uwsgi`_ to interface python and nginx, in your venv execute the following::

  wget https://projects.unbit.it/downloads/uwsgi-2.0.17.1.tar.gz
  tar zxvf uwsgi-2.0.17.1.tar.gz
  cd uwsgi-2.0.17.1
  ~/python2.7/bin/python uwsgiconfig.py --build
  ~/python2.7/bin/python uwsgiconfig.py  --plugin plugins/python core
  cp python_plugin.so ~/envs/python/bin/
  cp uwsgi ~/envs/python/bin/

  cd ..
  cp -r ~/mozdef/rest   ~/envs/mozdef/
  cp -r ~/mozdef/loginput   ~/envs/mozdef/

  cd ~/envs/mozdef/rest
  # modify config file
  vim index.conf
  # modify restapi.ini with any changes to pathing or number of processes you might need for your use case.
  vim restapi.ini

  cd ../loginput
  # modify loginput.ini with any changes to pathing or number of processes you might need for your use case.
  vim loginput.ini

Alternatively, if you do not wish to use the systemd unit files for starting these processes
you can start the restapi and loginput processes from within your venv via::

  cd /opt/mozdef/envs/python
  source bin/activate
  (mozdef) [mozdef@mozdev mozdef]$ uwsgi --ini rest/restapi.ini
  (mozdef) [mozdef@mozdev mozdef]$ uwsgi --ini loginput/loginput.ini

  sudo cp nginx.conf /etc/nginx
  # modify /etc/nginx/nginx.conf to reflect your server, and any path changes you've made.
  sudo vim /etc/nginx/nginx.conf
  # move uwsgi_params file into venv.
  cp /etc/nginx/uwsgi_params /opt/mozdef/envs/python/bin/
  sudo service nginx restart

.. _uwsgi: https://uwsgi-docs.readthedocs.io/en/latest/


Supervisord
***********

We use supervisord to run the alerts and alertactions. If you plan on starting services manually, you can skip this step.

To install supervisord perform the following as the user mozdef::

    cd /opt/mozdef/envs/python
    source bin/activate
    cd bin
    pip install supervisor

Within the alerts directory there is a supervisord_alerts.ini which is preconfigured.
If you've changed any directory paths for this installation then modify it to reflect your pathing changes.
There are systemd files in the systemdfiles directory that you can use to start the mozdefalerts and mozdefalertactions processes which we cover near the end of this tutorial.


ElasticSearch
*************

This section explains the manual installation process for Elasticsearch nodes (search and storage).
MozDef supports Elasticsearch version 5.x

Installation instructions are available on `Elasticsearch website`_.
You should prefer packages over archives if one is available for your distribution.

Add the repo in /etc/yum/repos.d/elasticsearch.repo::

  [elasticsearch-5.x]
  name=Elasticsearch repository for 5.x packages
  baseurl=https://artifacts.elastic.co/packages/5.x/yum
  gpgcheck=1
  gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
  enabled=1
  autorefresh=1
  type=rpm-md

  sudo yum install elasticsearch

.. _Elasticsearch website: https://www.elastic.co/products/elasticsearch

Marvel plugin
*************

`Marvel`_ is a monitoring plugin developed by Elasticsearch (the company).

WARNING: this plugin is NOT open source. At the time of writing, Marvel is free for 30 days.
After which you can apply for a free basic license to continue using it for it's key monitoring features.

To install Marvel, on each of your elasticsearch node, from the Elasticsearch home directory::

  sudo bin/plugin install license
  sudo bin/plugin install marvel-agent
  sudo service elasticsearch restart

You should now be able to access to Marvel at http://any-server-in-cluster:9200/_plugin/marvel

.. _Marvel: https://www.elastic.co/guide/en/marvel/current/introduction.html

Kibana
******

`Kibana`_ is a webapp to visualize and search your Elasticsearch cluster data::

Create the Repo in /etc/yum/repos.d/kibana.repo::

  [kibana-5.x]
  name=Kibana repository for 5.x packages
  baseurl=https://artifacts.elastic.co/packages/5.x/yum
  gpgcheck=1
  gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
  enabled=1
  autorefresh=1
  type=rpm-md

::

  sudo yum install kibana

Now you'll need to configure kibana to work with your system:
You can set the various settings in /etc/kibana/kibana.yml.
Some of the settings you'll want to configure are:

* server.name (your server's hostname)
* elasticsearch.url (the url to your elasticsearch instance and port)
* logging.dest ( /path/to/kibana.log so you can easily troubleshoot any issues)

Then you can start the service!

  service kibana start

.. _Kibana: https://www.elastic.co/products/kibana

Start Services
**************

To use the included systemd files you'll copy them to your system's default directory of /etc/systemd/system/.
Ensure it has root file permissions so that systemd can start it::

  cp /opt/mozdef/systemdfiles/web/mozdefweb.service /etc/systemd/system/
  cp /opt/mozdef/systemdfiles/web/mozdefrestapi.service /etc/systemd/system/
  cp /opt/mozdef/systemdfiles/web/mongod.service /etc/systemd/system/
  cp /opt/mozdef/systemdfiles/consumer/mozdefloginput.service /etc/systemd/system/
  cp /opt/mozdef/systemdfiles/consumer/mworker-eventtask.service /etc/systemd/system/
  cp /opt/mozdef/systemdfiles/alert/mozdefalerts.service /etc/systemd/system/
  cp /opt/mozdef/systemdfiles/alert/mozdefbot.service /etc/systemd/system/
  cp /opt/mozdef/systemdfiles/alert/mozdefalertactions.service /etc/systemd/system/

Then you will need to enable them::

  systemctl enable mozdefweb.service
  systemctl enable mozdefrestapi.service
  systemctl enable mozdefloginput.service
  systemctl enable mworker-eventtask.service
  systemctl enable mozdefalerts.service
  systemctl enable mozdefbot.service
  systemctl enable mozdefalertactions.service
  systemctl enable mongod.service

Reload systemd::

  systemctl daemon-reload

Now you can start your services::

  systemctl start mongod
  systemctl start mozdefalerts
  systemctl start mozdefbot
  systemctl start mozdefloginput
  systemctl start mozdefrestapi
  systemctl start mozdefweb
  systemctl start mworker-eventtask
  systemctl start mozdefalertactions


Alternatively you can start the following services manually in this way from inside the venv as mozdef::

  # Eventtask worker
  cd ~/MozDef/mq
  (mozdef) [mozdef@mozdev mq]$ uwsgi --ini eventtask.ini

  # alert worker
  (mozdef) [mozdef@mozdev mozdef]$ cd ~/mozdef/alerts
  (mozdef) [mozdef@mozdev alerts]$ celery -A celeryconfig worker --loglevel=info --beat

To initialize elasticsearch indices and load some sample data::

  (mozdef) [mozdef@mozdev mozdef]$ cd examples/es-docs/
  (mozdef) [mozdef@mozdev es-docs]$ python inject.py

To add more sample data you can run the following from inside the venv::

  (mozdef) [mozdef@mozdev mozdef]$ cd ~/mozdef/examples/demo
  (mozdef) [mozdef@mozdev demo]$ ./syncalerts.sh
  (mozdef) [mozdef@mozdev demo]$ ./sampleevents.sh

