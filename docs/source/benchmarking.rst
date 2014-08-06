Benchmarking
============

Performance is important for a SIEM because it's where you want to store, search and analyze all your security events.

You will want it to handle a significant number of new events per second, be able to search quickly and perform fast correlation.
Therefore, we provide some benchmarking scripts for MozDef to help you determine the performance of your setup. Performance tuning of elastic search can be complex and we highly recommend spending time tuning your environment.


Elasticsearch
-------------

Elasticsearch is the main backend component of MozDef.
We strongly recommend you to have a 3+ nodes cluster to allow recovery and load balancing.
During our tests, Elasticsearch recovered well after being pushed to the limits of hardware, loosing and regaining nodes, and a variety of valid/invalid data. We provide the following scripts for you to use to test your own implementation.

The scripts for Elasticsearch benchmarking are in `benchmarking/es/`.
They use `nodejs`_ to allow asynchronous HTTP requests.

.. _nodejs: http://nodejs.org/

insert_simple.js
****************

`insert_simple.js` sends indexing requests with 1 log/request.

Usage: `node ./insert_simple.js <processes> <totalInserts> <host1> [host2] [host3] [...]`

  * `processes`: Number of processes to spawn
  * `totalInserts`: Number of inserts to perform, please note after a certain number node will slow down. You want to have a lower number if you are in this case.
  * `host1`, `host2`, `host3`, etc: Elasticsearch hosts to which you want to send the HTTP requests

insert_bulk.js
**************

`insert_bulk.js` sends bulk indexing requests (several logs/request).

Usage: `node ./insert_bulk.js <processes> <insertsPerQuery> <totalInserts> <host1> [host2] [host3] [...]`

  * `processes`: Number of processes to spawn
  * `insertsPerQuery`: Number of logs per request
  * `totalInserts`: Number of inserts to perform, please note after a certain number node will slow down. You want to have a lower number if you are in this case.
  * `host1`, `host2`, `host3`, etc: Elasticsearch hosts to which you want to send the HTTP requests

search_all_fulltext.js
**********************

`search_all_fulltext.js` performs search on all indices, all fields in fulltext. It's very stupid.

Usage: `node ./search_all_fulltext.js <processes> <totalSearches> <host1> [host2] [host3] [...]`

  * `processes`: Number of processes to spawn
  * `totalSearches`: Number of search requests to perform, please note after a certain number node will slow down. You want to have a lower number if you are in this case.
  * `host1`, `host2`, `host3`, etc: Elasticsearch hosts to which you want to send the HTTP requests


