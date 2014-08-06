Code
====

Plugins
-------

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




.. _plugins: https://github.com/jeffbryner/MozDef/tree/master/mq/plugins



