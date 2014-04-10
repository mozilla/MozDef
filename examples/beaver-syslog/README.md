# beaver-syslog

This configuration for [beaver](https://github.com/josegonzalez/beaver) ships syslog logs stored in `/var/log/syslog/systems/myhost.example.com/*.log` to mozdef.

To run it:

```
beaver -c config.ini -t stdout
```
