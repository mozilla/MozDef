Match/Query Classes
-------------------

ExistsMatch
^^^^^^^^^^^

Checks to see if a specific field exists in a document

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import ExistsMatch

   ExistsMatch("randomfield")


TermMatch
^^^^^^^^^

Checks if a specific field matches the key

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import TermMatch

   TermMatch("details.ip", "127.0.0.1")


TermsMatch
^^^^^^^^^^

Checks if a specific field matches any of the keys

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import TermsMatch

   TermsMatch("details.ip", ["127.0.0.1", "1.2.3.4"])


WildcardMatch
^^^^^^^^^^^^^

Allows regex to be used in looking for documents that a field contains all or part of a key

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import WildcardMatch

   WildcardMatch('summary', 'test*')


PhraseMatch
^^^^^^^^^^^

Checks if a field contains a specific phrase (includes spaces)

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import PhraseMatch

   PhraseMatch('summary', 'test run')


BooleanMatch
^^^^^^^^^^^^

Used to apply specific "matchers" to a query. This will unlikely be used outside of SearchQuery.

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import ExistsMatch, TermMatch, BooleanMatch

   must = [
       ExistsMatch('details.ip')
   ]
   must_not = [
       TermMatch('type', 'alert')
   ]

   BooleanMatch(must=must, should=[], must_not=must_not)


MissingMatch
^^^^^^^^^^^^

Checks if a field does not exist in a document

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import MissingMatch

   MissingMatch('summary')


RangeMatch
^^^^^^^^^^

Checks if a field value is within a specific range (mostly used to look for documents in a time frame)

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import RangeMatch

   RangeMatch('utctimestamp', "2016-08-12T21:07:12.316450+00:00", "2016-08-13T21:07:12.316450+00:00")


QueryStringMatch
^^^^^^^^^^^^^^^^

Uses a custom query string to generate the "match" based on (Similar to what you would see in kibana)

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import QueryStringMatch

   QueryStringMatch('summary: test')


SubnetMatch
^^^^^^^^^^^^^^^^

Checks if an IP field is within the bounds of a subnet

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import SubnetMatch

   SubnetMatch('details.sourceipaddress', '10.1.1.0/24')


Aggregation
^^^^^^^^^^^

Used to aggregate results based on a specific field

.. code-block:: python
   :linenos:

   from mozdef_util.query_models import Aggregation, SearchQuery, ExistsMatch

   search_query = SearchQuery(hours=24)
   must = [
       ExistsMatch('seenindicator')
   ]
   search_query.add_must(must)
   aggr = Aggregation('details.ip')
   search_query.add_aggregation(aggr)
   results = search_query.execute(es_client, indices=['events','events-previous'])
