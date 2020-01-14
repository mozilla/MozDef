Simple test
--------------

If you want to just post some sample json to Mozdef do something like

.. code-block:: sh

    curl -v --header "Content-Type: application/json"   --request POST   --data '{"tags": ["test"],"summary": "just a test"}'   http://localhost:8080/events

where http://localhost:8080 is whatever is running the 'loginput' service.
The 'data' curl option is what gets posted as json to MozDef. If your post is successful, you should then be able to find the event in elastic search/kibana.
