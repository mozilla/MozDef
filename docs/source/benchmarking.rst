Benchmarking
============

Performance is important for a SIEM because it's where you want to see and analyze all your security events.

You probably want it to handle a lot of new messages per second, be able to have a fast reply when you search and have fast correlation.
Therefore, we provide some benchmarking scripts for MozDef to help you determine the performance of your setup.


Elasticsearch
-------------

Elasticsearch is the main backend component of MozDef.
We strongly recommend you to have a 3+ nodes cluster to allow recovery and load balancing.
During our tests, Elasticsearch recovered well after being hit too much.

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


