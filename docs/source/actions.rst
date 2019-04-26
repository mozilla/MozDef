Actions
=======

Actions are currently supported at the end of the alert pipeline.

Alert Action Processing
-----------------------

Alert actions run at the very end of the alert pipeline after the alert is already created, and are non blocking (meaning they also don't have the ability to modify alerts inline).

::

    class message(object):
        def __init__(self):
            '''
            triggers when a geomodel alert is generated
            '''
            self.alert_classname = 'AlertGeomodel'
            self.registration = 'geomodel'
            self.priority = 1


Alert Trigger
^^^^^^^^^^^^^

::

    def onMessage(self, message):
        print(message)
        return message


Plugin Registration
^^^^^^^^^^^^^^^^^^^

Simply place the .py file in the `alert actions`_ directory.

.. _alert actions: https://github.com/mozilla/MozDef/tree/master/alerts/actions
