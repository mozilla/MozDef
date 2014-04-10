Docker-MozDef
=============

Automated build of "MozDef: The Mozilla Defense Platform" with Docker.io

Dockerfile
----------
Use this to build a new image

	$ git clone https://github.com/2xyo/Docker-MozDef.git
    $ cd Docker-MozDef && sudo make build 

Running the container

    $ && sudo make run .

Now go to:

 * http://127.0.0.1:3000 < meteor
 * http://127.0.0.1:9090 < kibana
 * http://127.0.0.1:9200 < elasticsearch
 * http://127.0.0.1:9200/\_plugin/marvel < marvel (monitoring for elasticsearch)
 * http://127.0.0.1:8080 < loginput
 * http://127.0.0.1:8081 < rest api

Known issues
------------

* Marvel doesn't display node info: ` Oops! FacetPhaseExecutionException[Facet [fs.total.available_in_bytes]: failed to find mapping for fs.total.available_in_bytes]`

Marvel uses techniques to gather system info that are not compatible with docker.
See https://groups.google.com/forum/#!topic/elasticsearch/dhpxaOuoZWI

Despite this issue, marvel runs fine.


