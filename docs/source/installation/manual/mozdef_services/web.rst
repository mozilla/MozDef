Web Services
============

Meteor
******

`Meteor`_ is a javascript framework used for the realtime aspect of the web interface.

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
.. _meteor-accounts: https://guide.meteor.com/accounts.html


Node
****

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

We use the `nginx`_ webserver to serve the Web UI, Kibana, RestAPI, and Loginput::

  yum install nginx

.. _nginx: http://nginx.org/


Kibana
******

`Kibana`_ is a webapp to visualize and search your Elasticsearch cluster data

Create the repo file in /etc/yum/repos.d/kibana.repo::

  [kibana-5.x]
  name=Kibana repository for 5.x packages
  baseurl=https://artifacts.elastic.co/packages/5.x/yum
  gpgcheck=1
  gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
  enabled=1
  autorefresh=1
  type=rpm-md

::

  yum install kibana

Now you'll need to configure kibana to work with your system:
You can set the various settings in /etc/kibana/kibana.yml.
Some of the settings you'll want to configure are:

* server.name (your server's hostname)
* elasticsearch.url (the url to your elasticsearch instance and port)
* logging.dest ( /path/to/kibana.log so you can easily troubleshoot any issues)

Then you can start the service::

  service kibana start
  service kibana enable

.. _Kibana: https://www.elastic.co/products/kibana

RestAPI
*******

Crontab
*******