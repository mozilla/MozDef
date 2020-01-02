Final Steps
***********

Mozdef provides a utility script to populate the initial Elasticsearch indexes::

  source /opt/mozdef/envs/python/bin/activate
  cd /opt/mozdef/envs/mozdef/scripts
  python initial_setup.py http://localhost:9200 http://localhost:5601

