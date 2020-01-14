Web
***

`Meteor`_ is a javascript framework used for the realtime aspect of the web interface.

Install requirements::

  export NODE_VERSION=8.11.4
  export METEOR_VERSION=1.8

  cd /opt/mozdef
  gpg="gpg --no-default-keyring --secret-keyring /dev/null --keyring /dev/null --no-option --keyid-format 0xlong"
  rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7
  rpm -qi gpg-pubkey-f4a80eb5 | $gpg | grep 0x24C6A8A7F4A80EB5
  curl --silent --location https://rpm.nodesource.com/setup_8.x | bash -
  rpmkeys --import /etc/pki/rpm-gpg/NODESOURCE-GPG-SIGNING-KEY-EL
  rpm -qi gpg-pubkey-34fa74dd | $gpg | grep 0x5DDBE8D434FA74DD
  yum install -y \
     make \
     glibc-devel \
     gcc \
     gcc-c++ \
     libstdc++ \
     zlib-devel \
     nodejs
  curl --silent --location https://static-meteor.netdna-ssl.com/packages-bootstrap/$METEOR_VERSION/meteor-bootstrap-os.linux.x86_64.tar.gz \
    | tar --extract --gzip --directory /opt/mozdef .meteor
  ln --symbolic /opt/mozdef/.meteor/packages/meteor-tool/*/mt-os.linux.x86_64/scripts/admin/launch-meteor /usr/bin/meteor
  install --owner mozdef --group mozdef --directory /opt/mozdef/envs /opt/mozdef/envs/mozdef
  chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/meteor
  chown -R mozdef:mozdef /opt/mozdef/.meteor


Let's edit the configuration file::

  vim /opt/mozdef/envs/mozdef/meteor/imports/settings.js


.. note:: We'll need to modify the rootURL and kibanaURL variables in settings.js


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

In addition, environment variables can also be set instead of requiring modification of the settings.js file.:

::

    OPTIONS_METEOR_ROOTURL is "http://localhost" by default and should be set to the dns name of the UI where you will run MozDef
    OPTIONS_METEOR_PORT is 80 by default and is the port on which the UI will run
    OPTIONS_METEOR_ROOTAPI is http://rest:8081 by default and should resolve to the location of the rest api
    OPTIONS_METEOR_KIBANAURL is http://localhost:9090/app/kibana# by default and should resolve to your kibana installation
    OPTIONS_METEOR_ENABLECLIENTACCOUNTCREATION is true by default and governs whether accounts can be created
    OPTIONS_METEOR_AUTHENTICATIONTYPE is meteor-password by default and can be set to oidc to allow for oidc authentication
    OPTIONS_REMOVE_FEATURES is empty by default, but if you pass a comma separated list of features you'd like to remove they will no longer be available.


Install mozdef meteor project::

  su mozdef
  export MONGO_URL=mongodb://localhost:3002/meteor
  export ROOT_URL=http://localhost
  export PORT=3000

  mkdir -p /opt/mozdef/envs/meteor/mozdef
  cd /opt/mozdef/envs/mozdef/meteor
  meteor npm install
  meteor build --server localhost:3002 --directory /opt/mozdef/envs/meteor/mozdef
  ln --symbolic /opt/mozdef/envs/meteor/mozdef/node_modules /opt/mozdef/envs/mozdef/meteor/node_modules
  cd /opt/mozdef/envs/meteor/mozdef/bundle/programs/server
  npm install


Copy over systemd file (as root)::

  cp /opt/mozdef/envs/mozdef/systemdfiles/web/mozdefweb.service /usr/lib/systemd/system/mozdefweb.service
  systemctl daemon-reload

Start loginput service::

  systemctl start mozdefweb
  systemctl enable mozdefweb

.. _Meteor: https://guide.meteor.com/
