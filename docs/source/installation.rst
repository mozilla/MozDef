Installation
============

The installation process has been tested on CentOS 6, RHEL 6 and Ubuntu 14.

Docker
------

You can quickly install MozDef with an automated build generation using `docker`_.


Single Container
****************

MozDef can run in a single docker container, which uses supervisord to handle executing all of the MozDef processes. In order to run a single container::

  make single-build
  make single-run
  make single-stop # When you want to stop the container

You're done! Now go to:

 * http://localhost < meteor (main web interface)
 * http://localhost:9090/app/kibana < kibana
 * http://localhost:9200 < elasticsearch
 * http://localhost:8080 < loginput
 * http://localhost:8081 < rest api


Multiple Containers
*******************

Since MozDef consists of many processes running at once, we also support running MozDef with each process given it's own container. This can be useful during development, since you can turn off a single process to debug/troubleshoot while maintaining a functioning MozDef environment.
In order to run in multiple containers::

  make multiple-build
  make multiple-run
  make multiple-stop # When you want to stop the containers

You're done! Now go to:

 * http://localhost < meteor (main web interface)
 * http://localhost:9090/app/kibana < kibana
 * http://localhost:9200 < elasticsearch
 * http://localhost:8080 < loginput
 * http://localhost:8081 < rest api

.. _docker: https://www.docker.io/


MozDef manual installation process on RedHat systems
----------------------------------------------------

Summary
*******
This section explains the manual installation process for the MozDef system.
  git clone https://github.com/mozilla/MozDef.git



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

WARNING: this plugin is NOT open source. At the time of writing, Marvel is free for 30 days.
After which you can apply for a free basic license to continue using it for it's key monitoring features.

To install Marvel, on each of your elasticsearch node, from the Elasticsearch home directory::

  sudo bin/plugin install license
  sudo bin/plugin install marvel-agent
  sudo service elasticsearch restart

You should now be able to access to Marvel at http://any-server-in-cluster:9200/_plugin/marvel

.. _Marvel: https://www.elastic.co/guide/en/marvel/current/introduction.html

Web and Workers nodes
---------------------

This section explains the manual installation process for Web and Workers nodes.

Python
******

Create a mozdef user::

  adduser mozdef -d /opt/mozdef

We need to install a python2.7 virtualenv.

On Yum-based systems::

  sudo yum install make zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel pcre-devel gcc gcc-c++ mysql-devel

On APT-based systems::

  sudo apt-get install make zlib1g-dev libbz2-dev libssl-dev libncurses5-dev libsqlite3-dev libreadline-dev tk-dev libpcre3-dev libpcre++-dev build-essential g++ libmysqlclient-dev

Then::

  su - mozdef
  wget https://www.python.org/ftp/python/2.7.11/Python-2.7.11.tgz
  tar xvzf Python-2.7.11.tgz
  cd Python-2.7.11
  ./configure --prefix=/opt/mozdef/python2.7 --enable-shared
  make
  make install

  cd /opt/mozdef

  wget https://bootstrap.pypa.io/get-pip.py
  export LD_LIBRARY_PATH=/opt/mozdef/python2.7/lib/
  ./python2.7/bin/python get-pip.py
  ./python2.7/bin/pip install virtualenv
  mkdir ~/envs
  cd ~/envs
  ~/python2.7/bin/virtualenv mozdef
  source mozdef/bin/activate
  pip install -r MozDef/requirements.txt

At this point when you launch python, It should tell you that you're using Python 2.7.11.

Whenever you launch a python script from now on, you should have your mozdef virtualenv actived and your LD_LIBRARY_PATH env variable should include /opt/mozdef/python2.7/lib/

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

  chkconfig rabbitmq-server on

On APT-based systems ::

  sudo apt-get install rabbitmq-server
  sudo invoke-rc.d rabbitmq-server start

.. _RabbitMQ: https://www.rabbitmq.com/
.. _EPEL repos: http://fedoraproject.org/wiki/EPEL/FAQ#howtouse

Meteor
******

`Meteor`_ is a javascript framework used for the realtime aspect of the web interface.

We first need to install `Mongodb`_ since it's the DB used by Meteor.

On Yum-based systems:

In /etc/yum.repo.d/mongo, add::

  [mongodb]
  name=MongoDB Repository
  baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64/
  gpgcheck=0
  enabled=1

Then you can install mongodb::

  sudo yum install mongodb

On APT-based systems::

  sudo apt-get install mongodb-server

For meteor, in a terminal::

  curl https://install.meteor.com/ | sh

  wget https://nodejs.org/dist/v4.7.0/node-v4.7.0.tar.gz
  tar xvzf node-v4.7.0.tar.gz
  cd node-v4.7.0
  ./configure
  make
  sudo make install

Then from the meteor subdirectory of this git repository (/opt/mozdef/MozDef/meteor) run::

  meteor add iron-router

If you wish to use meteor as the authentication handler you'll also need to install the Accounts-Password pkg::

  meteor add accounts-password

You may want to edit the app/lib/settings.js file to properly configure the URLs and Authentication
The default setting will use Meteor Accounts, but you can just as easily install an external provider like Github, Google, Facebook or your own OIDC::

  mozdef = {
    rootURL: "localhost",
    port: "443",
    rootAPI: "https://localhost:8444",
    kibanaURL: "https://localhost:9443/app/kibana#",
    enableBlockIP: true,
    enableClientAccountCreation: true,
    authenticationType: "meteor-password"
  }

or for an OIDC implementation that passes a header to the nginx reverse proxy (for example using OpenResty with Lua and Auth0)::

  mozdef = {
    rootURL: "localhost",
    port: "443",
    rootAPI: "https://localhost:8444",
    kibanaURL: "https://localhost:9443/app/kibana#",
    enableBlockIP: true,
    enableClientAccountCreation: false,
    authenticationType: "OIDC"
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
    wget https://nodejs.org/dist/v4.7.0/node-v4.7.0.tar.gz
    tar xvfz node-v4.7.0.tar.gz
    cd node-v4.7.0
    python configure
    make
    make install

Then bundle the meteor portion of mozdef::

  cd <your meteor mozdef directory>
  meteor bundle mozdef.tgz

You can then deploy the meteor UI for mozdef as necessary::

  scp mozdef.tgz to your target host
  tar -xvzf mozdef.tgz

This will create a 'bundle' directory with the entire UI code below that directory.

If you didn't update the settings.js before bundling the meteor installation, you will need to update the settings.js file to match your servername/port::

  vim bundle/programs/server/app/app/lib/settings.js

If your development OS is different than your production OS you will also need to update
the fibers node module::

  cd bundle/programs/server/node_modules
  rm -rf fibers
  sudo npm install fibers@1.0.1

There are systemd unit files available in the systemd directory of the public repo you can use to start meteor using node.
If you aren't using systemd, then run the mozdef UI via node manually::

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
 baseurl=http://nginx.org/packages/OS/OSRELEASE/$basearch/
 gpgcheck=0
 enabled=1

.. _nginx: http://nginx.org/

UWSGI
*****

We use `uwsgi`_ to interface python and nginx::

  wget https://projects.unbit.it/downloads/uwsgi-2.0.12.tar.gz
  tar zxvf uwsgi-2.0.12.tar.gz
  cd uwsgi-2.0.12
  ~/python2.7/bin/python uwsgiconfig.py --build
  ~/python2.7/bin/python uwsgiconfig.py  --plugin plugins/python core
  cp python_plugin.so ~/envs/mozdef/bin/
  cp uwsgi ~/envs/mozdef/bin/

  cp -r ~/MozDef/rest   ~/envs/mozdef/
  cp -r ~/MozDef/loginput   ~/envs/mozdef/
  mkdir ~/envs/mozdef/logs

  cd ~/envs/mozdef/rest
  # modify config file
  vim index.conf
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

.. _uwsgi: https://uwsgi-docs.readthedocs.io/en/latest/

Kibana
******

`Kibana`_ is a webapp to visualize and search your Elasticsearch cluster data::

  wget https://download.elastic.co/kibana/kibana/kibana-4.6.2-linux-x86_64.tar.gz
  tar xvzf kibana-4.6.2-linux-x86_64.tar.gz
  ln -s kibana-4.6.2 kibana
  # configure /etc/nginx/nginx.conf to target this folder
  sudo service nginx reload

To initialize elasticsearch indices and load some sample data::

  cd examples/es-docs/
  python inject.py

.. _Kibana: https://www.elastic.co/products/kibana

Start Services
**************

TO DO: Add in services like supervisord, and refer to systemd files.

Start the following services

  cd ~/MozDef/mq
  ./esworker.py

  cd ~/MozDef/alerts
  celery -A celeryconfig worker --loglevel=info --beat

  cd ~/MozDef/examples/demo
  ./syncalerts.sh
  ./sampleevents.sh

Manual Installation
--------------------

*Use sudo whereever required*

**(Currently only for apt-based systems)**


1. Cloning repository ::

    $ export MOZDEF_PATH=/opt/MozDef
    $ git clone https://github.com/mozilla/MozDef.git $MOZDEF_PATH

2. Installing dependencies ::

    # RabbitMQ
    $ apt-get install -y rabbitmq-server
    $ rabbitmq-plugins enable rabbitmq_management

    # MongoDB
    $ apt-get install -y mongodb

    # NodeJS and NPM
    $ curl -sL https://deb.nodesource.com/setup_0.12 | sudo bash -
    $ apt-get install -y nodejs npm

    # Nginx
    $ apt-get install -y nginx-full
    $ cp $MOZDEF_PATH/docker/conf/nginx.conf /etc/nginx/nginx.conf

    # Libraries
    $ apt-get install -y python2.7-dev python-pip curl supervisor wget libmysqlclient-dev
    $ pip install -U pip

3. Installing python libraries ::

    $ pip install uwsgi celery virtualenv

    $ export PATH_TO_VENV=$HOME/.mozdef_env
    $ virtualenv $PATH_TO_VENV
    $ source $PATH_TO_VENV/bin/activate

    (.mozdef_env)$ pip install -r $MOZDEF_PATH/requirements.txt

4. Setting up uwsgi for rest and loginput ::

    $ mkdir /var/log/mozdef
    $ mkdir -p /run/uwsgi/apps/
    $ touch /run/uwsgi/apps/loginput.socket
    $ chmod 666 /run/uwsgi/apps/loginput.socket
    $ touch /run/uwsgi/apps/rest.socket
    $ chmod 666 /run/uwsgi/apps/rest.socket

5. Setting up local settings ::

    $ cp $MOZDEF_PATH/docker/conf/supervisor.conf /etc/supervisor/conf.d/supervisor.conf
    $ cp $MOZDEF_PATH/docker/conf/settings.js $MOZDEF_PATH/meteor/app/lib/settings.js
    $ cp $MOZDEF_PATH/docker/conf/config.py $MOZDEF_PATH/alerts/lib/config.py
    $ cp $MOZDEF_PATH/docker/conf/sampleData2MozDef.conf $MOZDEF_PATH/examples/demo/sampleData2MozDef.conf
    $ cp $MOZDEF_PATH/docker/conf/mozdef.localloginenabled.css $MOZDEF_PATH/meteor/public/css/mozdef.css

6. Installing Kibana ::

    $ cd /tmp/
    $ curl -L https://download.elastic.co/kibana/kibana/kibana-4.6.2-linux-x86_64.tar.gz | tar -C /opt -xz
    $ /bin/ln -s /opt/kibana-4.6.2 /opt/kibana
    $ cp $MOZDEF_PATH/examples/kibana/dashboards/alert.js /opt/kibana/app/dashboards/alert.js
    $ cp $MOZDEF_PATH/examples/kibana/dashboards/event.js /opt/kibana/app/dashboards/event.js

7. Installing Elasticsearch ::

    For Red Hat based:
    $ wget https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/rpm/elasticsearch/2.4.5/elasticsearch-2.4.5.rpm
    For Debian based:
    $ wget https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.5/elasticsearch-2.4.5.deb
    # You can download and install any version of ELasticSearch > 2.x and < 5.x

8. Setting up Meteor ::

    $ curl -L https://install.meteor.com/ | /bin/sh
    $ cd $MOZDEF_PATH/meteor
    $ meteor

9. Inserting some sample data ::

    # Elasticsearch server should be running
    $ service elasticsearch start
    $ source $PATH_TO_VENV/bin/activate
    (.mozdef_env)$ cd $MOZDEF_PATH/examples/es-docs && python inject.py

Start Services
***************

Start the following services ::

    $ invoke-rc.d rabbitmq-server start

    $ service elasticsearch start

    $ service nginx start

    $ uwsgi --socket /run/uwsgi/apps/loginput.socket --wsgi-file $MOZDEF_PATH/loginput/index.py --buffer-size 32768 --master --listen 100 --uid root --pp $MOZDEF_PATH/loginput --chmod-socket --logto /var/log/mozdef/uwsgi.loginput.log -H $PATH_TO_VENV

    $ uwsgi --socket /run/uwsgi/apps/rest.socket --wsgi-file $MOZDEF_PATH/rest/index.py --buffer-size 32768 --master --listen 100 --uid root --pp $MOZDEF_PATH/rest --chmod-socket --logto /var/log/mozdef/uwsgi.rest.log -H $PATH_TO_VENV

    $ cd $MOZDEF_PATH/mq && uwsgi --socket /run/uwsgi/apps/esworker.socket --mule=esworker.py --mule=esworker.py --buffer-size 32768 --master --listen 100 --uid root --pp $MOZDEF_PATH/mq --stats 127.0.0.1:9192  --logto /var/log/mozdef/uwsgi.esworker.log --master-fifo /run/uwsgi/apps/esworker.fifo -H $PATH_TO_VENV

    $ cd $MOZDEF_PATH/meteor && meteor run

    # Activate the virtualenv to run background jobs
    $ source $PATH_TO_VENV/bin/activate

    (.mozdef_env)$ cd $MOZDEF_PATH/alerts && celery -A celeryconfig worker --loglevel=info --beat
    (.mozdef_env)$ cd $MOZDEF_PATH/examples/demo && ./healthjobs.sh
    (.mozdef_env)$ cd $MOZDEF_PATH/examples/demo && ./sampleevents.sh
    (.mozdef_env)$ cd $MOZDEF_PATH/examples/demo && ./syncalerts.sh
