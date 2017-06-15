#!/usr/bin/env bash
/etc/init.d/nginx stop;
/etc/init.d/mozdefloginput stop;
/etc/init.d/mozdefmq stop;
/etc/init.d/mozdefrestapi stop;
killall -9 uwsgi;
/etc/init.d/mozdefloginput start;
/etc/init.d/nginx start;
/etc/init.d/mozdefmq start;
/etc/init.d/mozdefrestapi start