Demo Instance
=============

Mozilla used to maintain a demo instance of MozDef, however it's currently offline. Best bet for demo is to clone the repo and use the docker containers to stand up a local instance for yourself. There are some scripts in the https://github.com/mozilla/MozDef/tree/master/examples/demo folder to send sample events into a local docker instance that will generate alerts, attackers, etc and give you a feel for the flow.

First; set up your docker environment with some tweaks to avoid some common pitfalls: 

1) Allocate it at least 4GB of memory
2) Use the aufs filesystem driver ( to avoid issues unpacking tar files on overlayfs)

.. image:: https://user-images.githubusercontent.com/566889/47741098-ac306e80-dc36-11e8-88cb-4ba3f1458028.png
  :width: 40px
  :align: center
  :height: 100px


Once you've done that, here's how to make MozDef go using the provided docker compose files:

1) Pull the repo: git clone https://github.com/mozilla/MozDef.git
2) Run the containers:

  docker-compose -f docker/compose/docker-compose.yml  -p mozdef up

4) Firefox yourself to http://localhost to see the main UI (when the container starts)
5) Login using a locally created account (click login, create and choose a username/password)
