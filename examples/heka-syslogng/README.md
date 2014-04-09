# heka-syslogng

This configuration for [heka](http://hekad.readthedocs.org/en/latest/) ships syslog-ng logs stored in `/var/log/syslog/systems` to mozdef.

To run it:

```
rm -rf /var/cache/hekad/*
hekad -config=heka.toml
```
