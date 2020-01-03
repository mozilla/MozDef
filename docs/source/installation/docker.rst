Docker
======

.. note:: When using `docker` on Mac OS X, you may need to tweak Docker to use the aufs filesystem driver (to avoid issues unpacking tar files on overlayfs) `Changing Filesystem Driver <https://user-images.githubusercontent.com/566889/47741098-ac306e80-dc36-11e8-88cb-4ba3f1458028.png>`_

.. note:: MozDef consists of ~10 containers, so it's encouraged to have at least 4GB of memory provided to the Docker daemon.

If you have MozDef source code downloaded locally, you can build the docker containers locally::

  make build

If you want to use pre-built images that are on docker-hub::

  make build BUILD_MODE=pull

Start MozDef::

  make run

You're done! Now go to:

 * http://localhost < meteor (main web interface)
 * http://localhost:9090/app/kibana < kibana
 * http://localhost:8080 < loginput
 * http://localhost:514 < syslog input


If you want to stop MozDef::

  make stop


To cleanup all of the existing docker resources used by MozDef::

  make clean

.. _docker: https://www.docker.io/
