# nxlog-windows
First follow the installation instructions for [nxlog](http://nxlog.org/nxlog-docs/en/nxlog-reference-manual.html#quickstart_windows)
[nxlog download] (http://nxlog.org/download)

Edit the nxlog.conf file to match your environment, be sure to include the define ROOT stanza as described in the quick start.

Of importance to mozdef is the following: 

```
<Extension json>
Module xm_json
</Extension>
```
This loads the json converter module that takes everything in the windows event and parses it nicely to json. 


```
<Input in>
Module im_msvistalog
# For windows 2003 and earlier use the following:
# Module im_mseventlog
</Input>
```
This stanza sets up an input called 'in' that looks for the windows events.

```
<Output mozdef>
Module om_http
URL http://mozdef.servername.goes.here:8080/events/
Exec to_json();
</Output>

<Route 1>
Path in =>mozdef
</Route>
```
This stanza sets up the output called mozdef, picks an http endpoint that will use the json converter and sets up a route for the logs.

To start it simply start the Service Manager, find 'nxlog' in the list. Select it and start the service.

nxlog is very capable and can be used to route messages many places in a variety of formats, feel free to add routes to syslog, etc as needed.
