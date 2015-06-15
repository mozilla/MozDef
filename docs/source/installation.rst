Installation
============

The installation process has been tested on CentOS 6, RHEL 6 and Ubuntu 14.

Docker
------

You can quickly install MozDef with an automated build generation using `docker`_.

Dockerfile
***********

After `installing docker`_, use this to build a new image::

  cd docker && sudo make build

Running the container::

  sudo make run
  (once inside as root)
  /etc/init.d/supervisor start

You're done! Now go to:

 * http://localhost:3000 < meteor (main web interface)
 * http://localhost:9090 < kibana
 * http://localhost:9200 < elasticsearch
 * http://localhost:8080 < loginput
 * http://localhost:8081 < rest api

Get a terminal in the container
*******************************

An common problem in Docker is that once you start a container, you cannot enter it as there is no ssh by default.

When you make the container, you will enter it as root by default, but if you
would like to enter it manually use `nsenter` present in the `util-linux` > 2.23 package.
Debian and Ubuntu currently provide the 2.20 version so you need to download and compile the source code::

  cd /tmp
  curl https://www.kernel.org/pub/linux/utils/util-linux/v2.24/util-linux-2.24.tar.gz | tar -zxf-
  cd util-linux-2.24
  ./configure --without-ncurses
  make nsenter
  cp nsenter /usr/local/bin

Now we can create a script for docker (/usr/local/sbin/dkenter)::

  #!/bin/bash

  CNAME=$1
  CPID=$(docker inspect --format '{{ .State.Pid }}' $CNAME)
  nsenter --target $CPID --mount --uts --ipc --net --pid

While your MozDef container is running::

  docker ps # find the container ID, fc4917f00ead in this example
  dkenter fc4917f00ead
  root@fc4917f00ead:/# ...
  root@fc4917f00ead:/# exit

Docker config in AWS
--------------------

Summary
*******

If you don't want to install MozDef with docker on your own machine because for example it doesn't support docker or you fear you don't have enough memory, AWS supports docker.

1. Create a t2.small instance (enough to test MozDef) with the following details:

   * AMI: Ubuntu LTS-14-04 HVM
   * In "Configure Instance Details", expand the "Advanced Details" section. Under "User data", select "As text". Enter `#include https://get.docker.io` into the instance "User data". It will bootstrap docker in your instance boot.
2. In this instance, clone our github repo
3. Follow our docker config install `instructions`_
4. Configure your security group to open the ports you need. Keep in mind that it's probably a bad idea to have a public facing elasticsearch.

Detailed Steps
**************
Step by Step::

    Sign into AWS
    Choose EC2
    Choose Images->AMIs
    Find  Public Image ami-a7fdfee2 or a suitable Ubuntu 14.04 LTS(HVM) SSD 64bit server with HVM virtualization.
    Choose Launch
    Choose an instance type according to your budget. (at least a t2.small)
    Choose next: configure instance details
    Choose a network or create a VPC
    Choose or create a new subnet
    Choose to Assign a public IP
    Under advanced details: user data choose 'as text' and enter #include https://get.docker.io
    Choose next: add storage and add appropriate storage according to your budget
    Choose next and add any tags you may want
    Choose next and select any security group you may want to limit incoming traffic.
    Choose launch and select an ssh key-pair or create a new one for ssh access to the instance.

    For easy connect instructions, select your instance in the Ec2 dashboard->instances menu and choose connect for instructions.
    ssh into your new instance according to the instructions ^^

    clone the github repo to get the latest code:
    from your home directory (/home/ubuntu if using the AMI instance from above)
        sudo apt-get update
        sudo apt-get install git
        git clone https://github.com/jeffbryner/MozDef.git

    change the settings.js file to match your install:
    vim /home/ubuntu/MozDef/docker/conf/settings.js
        <change rootURL,rootAPI, kibanaURL from localhost to the FQDN or ip address of your AMI instance: i.e. http://1.2.3.4 >

    Inbound port notes:
    You will need to allow the AWS/docker instance to talk to the FQDN or ip address you specify in settings.js
    or the web ui will likely fail as it tries to contact internal services.
    i.e. you may need to setup custom TCP rules in your AWS security group to allow the instance to talk to itself
    if you use the public IP on the ports specified in settings.js. (usually 3000 for meteor, 8081 for rest api, 9090 for kibana and 9200 for kibana/ES)

    build docker:
        cd MozDef/docker
        sudo apt-get install make
        sudo make build (this will take awhile)
            [ make build-no-cache     (if needed use to disable docker caching routines or rebuild)
            [ at the end you should see a message like: Successfully built e8e075e66d8d ]

    starting docker:
        <build dkenter which will allow you to enter the docker container and control services, change settings, etc>
            sudo apt-get install gcc
            cd /tmp
            curl https://www.kernel.org/pub/linux/utils/util-linux/v2.24/util-linux-2.24.tar.gz | tar -zxf-
            cd util-linux-2.24
            ./configure --without-ncurses
            make nsenter
            sudo cp nsenter /usr/local/bin

            sudo vim /usr/local/bin/dkenter
                #!/bin/bash

                CNAME=$1
                CPID=$(docker inspect --format '{{ .State.Pid }}' $CNAME)
                nsenter --target $CPID --mount --uts --ipc --net --pid

            sudo chmod +x /usr/local/bin/dkenter

        cd && cd MozDef/docker/
        screen
        sudo make run
        (once inside the container)
        #/etc/init.d/supervisor start
        
        Browse to http://youripaddress:3000 for the MozDef UI

    Build notes:
    ************
    You can sign in using any Persona-enabled service (i.e. any yahoo or gmail account will work)
    supervisor config that starts everything is in /etc/supervisor/conf.d/supervisor.conf
    MozDef runs as root in /opt/MozDef
    Logs are in /var/log/mozdef
    MozDef will automatically start sending sample events to itself. To turn this off:
        0) get a new screen ( ctrl a c)
        1) sudo docker ps (to get the container id)
        2) sudo dkenter <containerid>
        3) supervisorctl
        4) stop realTimeEvents




.. _docker: https://www.docker.io/
.. _installing docker: https://docs.docker.com/installation/#installation
.. _instructions: http://mozdef.readthedocs.org/en/latest/installation.html#dockerfile

MozDef manual installation process
----------------------------------
This section explains the manual installation process for the MozDef system.
  git clone https://github.com/jeffbryner/MozDef.git



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

  sudo bin/plugin -i elasticsearch/marvel/latest
  sudo service elasticsearch restart

You should now be able to access to Marvel at http://any-server-in-cluster:9200/_plugin/marvel

.. _Marvel: http://www.elasticsearch.org/overview/marvel/

Web and Workers nodes
---------------------

This section explains the manual installation process for Web and Workers nodes.

Python
******

Create a mozdef user::

  adduser mozdef

We need to install a python2.7 virtualenv.

On Yum-based systems::

  sudo yum install make zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel pcre-devel gcc gcc-c++ mysql-devel

On APT-based systems::

  sudo apt-get install make zlib1g-dev libbz2-dev libssl-dev libncurses5-dev libsqlite3-dev libreadline-dev tk-dev libpcre3-dev libpcre++-dev build-essential g++ libmysqlclient-dev

Then::

  su - mozdef
  wget http://python.org/ftp/python/2.7.6/Python-2.7.6.tgz
  tar xvzf Python-2.7.6.tgz
  cd Python-2.7.6
  ./configure --prefix=/home/mozdef/python2.7 --enable-shared
  make
  make install

  cd /home/mozdef

  wget https://raw.github.com/pypa/pip/master/contrib/get-pip.py
  export LD_LIBRARY_PATH=/home/mozdef/python2.7/lib/
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

To install it, first make sure you enabled `EPEL repos`_. Then you need to install an Erlang environment.
On Yum-based systems::

  sudo yum install erlang

You can then install the rabbitmq server::

  sudo rpm --import http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
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

  wget http://nodejs.org/dist/v0.10.26/node-v0.10.26.tar.gz
  tar xvzf node-v0.10.26.tar.gz
  cd node-v0.10.26
  ./configure
  make
  sudo make install

Make sure you have meteorite/mrt (run as root/admin)::

  npm install -g meteorite

Then from the meteor subdirectory of this git repository (/home/mozdef/MozDef/meteor)  run::

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


Node
******

Alternatively you can run the meteor UI in 'deployment' mode using a native node installation.

First install node::

    yum install bzip2 gcc gcc-c++ sqlite sqlite-devel
    wget http://nodejs.org/dist/v0.10.25/node-v0.10.25.tar.gz
    tar xvfz node-v0.10.25.tar.gz
    cd node-v0.10.25
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

You will need to update the settings.js file to match your servername/port::

  vim bundle/programs/server/app/app/lib/settings.js

If your development OS is different than your production OS you will also need to update
the fibers node module::

  cd bundle/programs/server/node_modules
  rm -rf fibers
  sudo npm install fibers@1.0.1

Then run the mozdef UI via node::

  export MONGO_URL=mongodb://mongoservername:3002/meteor
  export ROOT_URL=http://meteorUIservername/
  export PORT=443
  node bundle/main.js


.. _Meteor: https://www.meteor.com/
.. _Mongodb: https://www.mongodb.org/

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
  baseurl=http://nginx.org/packages/centos/6/$basearch/
  gpgcheck=0
  enabled=1

.. _nginx: http://nginx.org/

UWSGI
*****

We use `uwsgi`_ to interface python and nginx::

  wget http://projects.unbit.it/downloads/uwsgi-2.0.2.tar.gz
  tar zxvf uwsgi-2.0.2.tar.gz
  cd uwsgi-2.0.2
  ~/python2.7/bin/python uwsgiconfig.py --build
  ~/python2.7/bin/python uwsgiconfig.py  --plugin plugins/python core
  cp python_plugin.so ~/envs/mozdef/bin/
  cp uwsgi ~/envs/mozdef/bin/

  cp -r ~/MozDef/rest   ~/envs/mozdef/
  cp -r ~/MozDef/loginput   ~/envs/mozdef/
  mkdir ~/envs/mozdef/logs

  cd ~/envs/mozdef/rest
  # modify settings.py
  vim settings.py
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

To initialize elasticsearch indices and load some sample data::

  cd examples/es-docs/
  python inject.py

.. _Kibana: http://www.elasticsearch.org/overview/kibana

Start Services
******

Start the following services

  cd ~/MozDef/mq
  ./esworker.py

  cd ~/MozDef/alerts
  celery -A celeryconfig worker --loglevel=info --beat

  cd ~/MozDef/examples/demo
  ./syncalerts.sh
  ./sampleevents.sh
