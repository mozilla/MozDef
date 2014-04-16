Code
====

Plugins
-------

The front-end event processing portion of MozDef supports python plugins to allow customization of the input chain. 
Plugins are simple python modules than can register for events with a priority, so they only see events with certain
dictionary items/values and will get them in a predefined order. 

To create a plugin, make a python class that presents a registration dictionary and a priority as follows: 

::

  class message(object):
      def __init__(self):
          '''register our criteria for being passed a message
             return a dict with fieldname:None to be sent anything with that field
             return a dict with fieldname:Value to be sent anything with that field/value
             return a string to be sent anything with any field matching that string evaluated as a regex.
             set the priority if you have a preference for order of plugins to run.
             0 goes first, 100 is assumed/default if not sent
          '''
          
          rdict = dict()
          rdict['details'] = dict()
          rdict['details']['sourceipaddress'] = None
          rdict['details']['destinationipaddress'] = None
          self.registration = rdict
          self.priority = 1
          

Message Processing
++++++++++++++++++

To process a message, define an onMessage function within your class as follows: 

::

    def onMessage(self, message):
        return message


The plugin will receive a copy of the incoming event as a python dictionary in the 'message' variable. The plugin can do
whatever it wants with this dictionary and return it to MozDef. Plugins will be called in priority order 1 to 100 if the 
incoming event matches their registration criteria. i.e. If you register for sourceipaddress you will only get events containing
the sourceipaddress field.


Plugin Registration
+++++++++++++++++++

Simply place the .py file in the plugins directory where the esworker.py is located, restart the esworker.py process
and it will recognize the plugin and pass it events as it sees them. 








