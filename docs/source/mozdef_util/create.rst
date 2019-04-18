Creating/Updating Documents
---------------------------

Create a new Event
^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   event_dict = {
       "example_key": "example value"
   }
   es_client.save_event(body=event_dict)

Update an existing event
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   event_dict = {
       "example_key": "example new value"
   }
   # Assuming 12345 is the id of the existing entry
   es_client.save_event(body=event_dict, doc_id="12345")

Create a new alert
^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   alert_dict = {
       "example_key": "example value"
   }
   es_client.save_alert(body=alert_dict)

Update an existing alert
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   alert_dict = {
       "example_key": "example new value"
   }
   # Assuming 12345 is the id of the existing entry
   es_client.save_alert(body=alert_dict, doc_id="12345")

Create a new generic document
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   document_dict = {
       "example_key": "example value"
   }
   es_client.save_object(index='randomindex', body=document_dict)

Update an existing document
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   document_dict = {
       "example_key": "example new value"
   }
   # Assuming 12345 is the id of the existing entry
   es_client.save_object(index='randomindex', body=document_dict, doc_id="12345")

Bulk Importing
^^^^^^^^^^^^^^

.. code-block:: python
   :linenos:

   from mozdef_util.elasticsearch_client import ElasticsearchClient
   es_client = ElasticsearchClient("http://127.0.0.1:9200", bulk_amount=30, bulk_refresh_time=5)
   es_client.save_event(body={'key': 'value'}, bulk=True)

- Line 2: bulk_amount (defaults to 100), specifies how many messages should sit in the bulk queue before they get written to elasticsearch
- Line 2: bulk_refresh_time (defaults to 30), is the amount of time that a bulk flush is forced
- Line 3: bulk (defaults to False) determines if an event should get added to a bulk queue
