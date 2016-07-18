Code
====

Plugins
-------

Plugins are supported in several places: Event Processing and the REST api.

Event Processing
================
The front-end event processing portion of MozDef supports python `plugins`_ to allow customization of the input chain. 
Plugins are simple python modules than can register for events with a priority, so they only see events with certain
dictionary items/values and will get them in a predefined order. 

To create a plugin, make a python class that presents a registration dictionary and a priority as follows: 

::

    class message(object):
        def __init__(self):
            '''register our criteria for being passed a message
               as a list of lower case strings or values to match with an event's dictionary of keys or values
               set the priority if you have a preference for order of plugins to run.
               0 goes first, 100 is assumed/default if not sent
            '''
            self.registration = ['sourceipaddress', 'destinationipaddress']
            self.priority = 20
          

Message Processing
++++++++++++++++++

To process a message, define an onMessage function within your class as follows: 

::

    def onMessage(self, message, metadata):
        #do something interesting with the message or metadata
        return (message, metadata)


The plugin will receive a copy of the incoming event as a python dictionary in the 'message' variable. The plugin can do whatever it wants with this dictionary and return it to MozDef. Plugins will be called in priority order 0 to 100 if the incoming event matches their registration criteria. i.e. If you register for sourceipaddress you will only get events containing the sourceipaddress field.

If you return the message as None (i.e. message=None) the message will be dropped and not be processed any further. 
If you modify the metadata the new values will be used when the message is posted to elastic search. You can use this
to assign custom document types, set static document _id values, etc. 


Plugin Registration
+++++++++++++++++++

Simply place the .py file in the plugins directory where the esworker.py is located, restart the esworker.py process
and it will recognize the plugin and pass it events as it sees them. 


REST Plugins
============

The REST API for MozDef also supports `python plugins`_ which allow you to customize your handling of API calls to suit your environment.
Plugins are simple python modules than can register for REST endpoints with a priority, so they only see calls for that endpoint
and will get them in a predefined order. 


To create a REST API plugin simply create a python class that presents a registration dictionary and priority as follows:

::

    class message(object):
        def __init__(self):
            '''register our criteria for being passed a message
               as a list of lower case strings to match with an rest endpoint
               (i.e. blockip matches /blockip)
               set the priority if you have a preference for order of plugins
               0 goes first, 100 is assumed/default if not sent
               
               Plugins will register in Meteor with attributes:
               name: (as below)
               description: (as below)
               priority: (as below)
               file: "plugins.filename" where filename.py is the plugin code.
               
               Plugin gets sent main rest options as:
               self.restoptions
               self.restoptions['configfile'] will be the .conf file
               used by the restapi's index.py file.
               
            '''
    
            self.registration = ['blockip']
            self.priority = 10
            self.name = "Banhammer"
            self.description = "BGP Blackhole"
        

The registration is the REST endpoint for which your plugin will receive a copy of the request/response objects to use or modify.
The priority allows you to order your plugins if needed so that they operate on data in a defined pattern.
The name and description are passed to the Meteor UI for use in dialog boxes, etc so the user can make choices when needed
to include/exclude plugins. For example the /blockip endpoint allows you to register multiple methods of blocking an IP
to match your environment: firewalls, BGP tables, DNS blackholes can all be independently implemented and chosen by the user
at run time.


Message Processing
++++++++++++++++++

To process a message, define an onMessage function within your class as follows:

::

    def onMessage(self, request, response):
        '''
        request: http://bottlepy.org/docs/dev/api.html#the-request-object
        response: http://bottlepy.org/docs/dev/api.html#the-response-object
        
        '''
        response.headers['X-PLUGIN'] = self.description


It's a good idea to add your plugin to the response headers if it acts on a message to facilitate troubleshooting.
Other than that, you are free to perform whatever processing you need within the plugin being sure to
return the request, response object once done:

::

    return (request, response)



Plugin Registration
+++++++++++++++++++

Simply place the .py file in the rest/plugins directory, restart the REST API process
and it will recognize the plugin and pass it events as it sees them. 



.. _plugins: https://github.com/jeffbryner/MozDef/tree/master/mq/plugins
.. _python plugins: https://github.com/jeffbryner/MozDef/tree/master/rest/plugins



