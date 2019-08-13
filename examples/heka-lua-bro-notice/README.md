# heka-lua-bro-notice

This configuration for [heka](https://hekad.readthedocs.org/en/latest/) ships notice logs for [Bro](https://bro.org/) stored in `/nsm/bro/spool/manager/notice.log` to mozdef.

We use here the [Lua Sandbox for heka](https://hekad.readthedocs.org/en/latest/sandbox/index.html) to parse our logs.

These log files have comments starting by `#` and have tab-delimited fields.

To run it:

```
rm -rf /var/cache/hekad/*
cp -rf bronotice.lua /usr/share/hekad
hekad -config=heka.toml
```
