# heka-apache

This configuration for [heka](https://hekad.readthedocs.org/en/latest/) ships apache logs stored in `/var/log/syslog/systems/web` to mozdef.

To run it:

```
rm -rf /var/cache/hekad/*
hekad -config=heka.toml
```
