Sending logs to MozDef
----------------------

Events/Logs are accepted as json over http(s) with the POST or PUT methods or over rabbit-mq.
Most modern log shippers support json output. MozDef is tested with support for:

* `heka`_
* `beaver`_
* `nxlog`_
* `logstash`_
* `rsyslog`_
* `native python code`_
* `AWS cloudtrail`_ (via native python)

We have `some configuration snippets`_

.. _heka: https://github.com/mozilla-services/heka
.. _beaver: https://github.com/josegonzalez/beaver
.. _nxlog: https://nxlog.org/download
.. _logstash: https://www.elastic.co/products/logstash
.. _rsyslog: https://www.rsyslog.com/doc/master/configuration/modules/omhttp.html
.. _native python code: https://github.com/gdestuynder/mozdef_lib
.. _AWS cloudtrail: https://aws.amazon.com/cloudtrail/
.. _some configuration snippets: https://github.com/mozilla/MozDef/tree/master/examples

What should I log?
******************

If your program doesn't log anything it doesn't exist. If it logs everything that happens it becomes like the proverbial boy who cried wolf. There is a fine line between logging too little and too much but here is some guidance on key events that should be logged and in what detail.

+------------------+---------------------------+---------------------------------------+
|    Event         |         Example           |               Rationale               |
+==================+===========================+=======================================+
| Authentication   | Failed/Success logins     | Authentication is always an important |
| Events           |                           | event to log as it establishes        |
|                  |                           | traceability for later events and     |
|                  |                           | allows correlation of user actions    |
|                  |                           | across systems.                       |
+------------------+---------------------------+---------------------------------------+
| Authorization    | Failed attempts to        | Once a user is authenticated they     |
| Events           | insert/update/delete a    | usually obtain certain permissions.   |
|                  | record or access a        | Logging when a user's permissions do  |
|                  | section of an application.| not allow them to perform a function  |
|                  |                           | helps troubleshooting and can also    |
|                  |                           | be helpful when investigating         |
|                  |                           | security events.                      |
+------------------+---------------------------+---------------------------------------+
| Account          | Account                   | Adding, removing or changing accounts |
| Lifecycle        | creation/deletion/update  | are often the first steps an attacker |
|                  |                           | performs when entering a system.      |
+------------------+---------------------------+---------------------------------------+
| Password/Key     | Password changed, expired,| If your application takes on the      |
| Events           | reset. Key expired,       | responsibility of storing a user's    |
|                  | changed, reset.           | password (instead of using a          |
|                  |                           | centralized source) it is             |
|                  |                           | important to note changes to a users  |
|                  |                           | credentials or crypto keys.           |
+------------------+---------------------------+---------------------------------------+
| Account          | Account lock, unlock,     | If your application locks out users   |
| Activations      | disable, enable           | after failed login attempts or allows |
|                  |                           | for accounts to be inactivated,       |
|                  |                           | logging these events can assist in    |
|                  |                           | troubleshooting access issues.        |
+------------------+---------------------------+---------------------------------------+
| Application      | Invalid input,            | If your application catches errors    |
| Exceptions       | fatal errors,             | like invalid input attempts on web    |
|                  | known bad things          | forms, failures of key components,    |
|                  |                           | etc creating a log record when these  |
|                  |                           | events occur can help in              |
|                  |                           | troubleshooting and tracking security |
|                  |                           | patterns across applications. Full    |
|                  |                           | stack traces should be avoided however|
|                  |                           | as the signal to noise ratio is       |
|                  |                           | often overwhelming.                   |
|                  |                           |                                       |
|                  |                           | It is also preferable to send a single|
|                  |                           | event rather than a multitude of      |
|                  |                           | events if it is possible for your     |
|                  |                           | application to correlate a significant|
|                  |                           | exception.                            |
|                  |                           |                                       |
|                  |                           | For example, some systems are         |
|                  |                           | notorious for sending a connection    |
|                  |                           | event with source IP, then sending an |
|                  |                           | authentication event with a session ID|
|                  |                           | then later sending an event for       |
|                  |                           | invalid input that doesn't include    |
|                  |                           | source IP or session ID or username.  |
|                  |                           | Correctly correlating these events    |
|                  |                           | across time is much more difficult    |
|                  |                           | than just logging all pieces of       |
|                  |                           | information if it is available.       |
+------------------+---------------------------+---------------------------------------+