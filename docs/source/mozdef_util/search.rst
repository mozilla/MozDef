Searching for documents
-----------------------

Simple search
^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import SearchQuery, TermMatch, ExistsMatch

   search_query = SearchQuery(hours=24)
   must = [
       TermMatch('category', 'brointel'),
       ExistsMatch('seenindicator')
   ]
   search_query.add_must(must)
   results = search_query.execute(es_client, indices=['events','events-previous'])

SimpleResults

When you perform a "simple" search (one without any aggregation), a SimpleResults object is returned. This object is a dict, with the following format:

.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Key
     - Description
   * - hits
     - Contains an array of documents that matched the search query
   * - meta
     - Contains a hash of fields describing the search query (Ex: if the query timed out or not)

Example simple result:

.. code-block:: text
   :linenos:

   {
    'hits': [
      {
        '_id': u'cp5ZsOgLSu6tHQm5jAZW1Q',
        '_index': 'events-20161005',
        '_score': 1.0,
        '_source': {
          'details': {
            'information': 'Example information'
          },
          'category': 'excategory',
          'summary': 'Test Summary',
          'type': 'event'
        }
      }
    ],
    'meta': {'timed_out': False}
   }


Aggregate search
^^^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import SearchQuery, TermMatch, Aggregation

   search_query = SearchQuery(hours=24)
   search_query.add_must(TermMatch('category', 'brointel'))
   search_query.add_aggregation(Aggregation('source'))
   results = search_query.execute(es_client)

AggregatedResults

When you perform an aggregated search (Ex: give me a count of all different ip addresses are in the documents that match a specific query), a AggregatedResults object is returned. This object is a dict, with the following format:


.. list-table::
   :widths: 25 50
   :header-rows: 1

   * - Key
     - Description
   * - aggregations
     - Contains the aggregation results, grouped by field name
   * - hits
     - Contains an array of documents that matched the search query
   * - meta
     - Contains a hash of fields describing the search query (Ex: if the query timed out or not)

.. code-block:: text
   :linenos:

   {
    'aggregations': {
       'ip': {
         'terms': [
           {
             'count': 2,
             'key': '1.2.3.4'
           },
           {
             'count': 1,
             'key': '127.0.0.1'
           }
         ]
       }
     },
     'hits': [
       {
         '_id': u'LcdS2-koQWeICOpbOT__gA',
         '_index': 'events-20161005',
         '_score': 1.0,
         '_source': {
           'details': {
             'information': 'Example information'
           },
           'ip': '1.2.3.4',
           'summary': 'Test Summary',
           'type': 'event'
         }
       },
       {
         '_id': u'F1dLS66DR_W3v7ZWlX4Jwg',
         '_index': 'events-20161005',
         '_score': 1.0,
         '_source': {
           'details': {
             'information': 'Example information'
           },
           'ip': '1.2.3.4',
           'summary': 'Test Summary',
           'type': 'event'
         }
       },
       {
         '_id': u'G1nGdxqoT6eXkL5KIjLecA',
         '_index': 'events-20161005',
         '_score': 1.0,
         '_source': {
           'details': {
             'information': 'Example information'
           },
           'ip': '127.0.0.1',
           'summary': 'Test Summary',
           'type': 'event'
         }
       }
     ],
     'meta': {
       'timed_out': False
     }
   }
