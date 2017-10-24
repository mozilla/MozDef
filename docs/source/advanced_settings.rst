Advanced Settings
=================

Conf files
----------
MozDef python scripts in almost all cases expect to be given a -c path/to/file.conf command line option to specify configuration/run time options.

These files all follow the same format:

::

    [options]
    setting1=value1
    setting2=value2


All programs do their best to set reasonable, sane defaults and most will run fine without a conf file. By default programname.py will look for programname.conf as it's configuration file so if you follow that convention you don't even need to specify the -c path/to/file.conf option.

Special Config Items
_____________________

Here are some tips for some key settings:

::

    [options]
    esservers=http://server1:9200,http://server2:9200,http://server3:9200

is how you can specify servers in your elastic search cluster.

::

    [options]
    backup_indices = intelligence,.kibana,alerts,events,complianceitems,.jsp,.marvel-kibana,vulnerabilities
    backup_dobackup = 1,1,1,1,1,1,1,1
    backup_rotation = none,none,monthly,daily,none,none,none,none
    backup_pruning = 0,0,0,20,0,0,0,0

is how you would configure the backupSnapshot.py and pruneIndexes.py programs to backup selected elastic search indexes, rotate selected indexes and prune certain indexes at selected intervals. In the case above we are backing up all indexes mentioned, rotating alerts monthly, rotating events daily and pruning events indices after 20 days.

::

    [options]
    autocategorize = True
    categorymapping = [{"bruteforce":"bruteforcer"},{"nothing":"nothing"}]

is how you would configure collectAttackers.py to do autocategoization of attackers that it discovers and specify a list of mappings matching alert categories to attacker category.

Myo with TLS/SSL
_____________________
MozDef supports the Myo armband to allow you to navigate the attackers scene using gestures. This works fine if meteor is hosted using http WITHOUT TLS/SSL as the browser will allow you to connect to the server and to the Myo connect which runs a local webserver at http://127.0.0.1:10138 by default. The browser makes a websocket connection to Myo connect and everyone is happy.

When hosting MozDef/Meteor on a TLS/SSL-enabled server things go south quickly. The browser doesn't like (or permit) a https:// hosted page from accessing a plain text websocket resource such as ws://127.0.0.1:10138.

Luckily you can use nginx to work around this.

On you local workstation you can setup a nginx reverse proxy to allow the browser to do TLS/SSL connections, and use nginx to redirect that 127.0.0.1 traffic from TLS to plain text Myo.  Here's some configs:

First in mozdef you need to add a myoURL option to settings.js:

::

    mozdef = {
      rootURL: "http://yourserver",
      port: "3000",
      rootAPI: "https://yourserver:8444/",
      enableBlockIP: true,
      kibanaURL: "http://yourkibanaserver:9090",
      myoURL: "wss://127.0.0.1:8444/myo/"
    }


This tells MozDef to initialize Myo using a local TLS connection to port 8444.

Now install nginx and set a nginx.conf file like so:

::

    http {
        include       mime.types;
        default_type  application/octet-stream;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 10m;
        ssl_certificate /path/to/localhost.crt;
        ssl_certificate_key /path/to/localhost.key;

        sendfile        on;
        keepalive_timeout  65;

        proxy_headers_hash_max_size 51200;
        proxy_headers_hash_bucket_size 6400;
        ##ssl version of myo connect##
        server{
            listen  *:8444 ssl;
            #access_log /dev/null main;
             location /{
                 proxy_pass http://127.0.0.1:10138;
                 proxy_read_timeout 90;
                 # WebSocket support (nginx 1.4)
                 proxy_http_version 1.1;
                 proxy_set_header Upgrade $http_upgrade;
                 proxy_set_header Connection "upgrade";
                 proxy_redirect     default;
             }
        }
    }

You'll need a SSL certificate that your browser trusts, you can issue a self-signed one and accept it by just browsing to https://127.0.0.1:8443 and accept the cert if necessary.

Start up MozDef, start up your Myo and enjoy!
