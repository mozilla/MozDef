# heka-lua-syslog

This configuration for [heka](http://hekad.readthedocs.org/en/latest/) ships syslog-style logs stored in `/var/log/syslog/systems` to mozdef.

To run it:

```
rm -rf /var/cache/hekad/*
cp -rf syslog_tab_delimited.lua /usr/share/hekad
hekad -config=heka.toml
```
