# heka-regex-syslog

This configuration for [heka](http://hekad.readthedocs.org/en/latest/) ships syslog-style logs stored in `/var/log/syslog/systems` to mozdef.

__WARNING__: This version is using a PayloadRegexDecoder which is way slower than the heka-lua-syslog snippet. So it shouldn't be used for production and is meant just as a snippet.

To run it:

```
rm -rf /var/cache/hekad/*
hekad -config=heka.toml
```
