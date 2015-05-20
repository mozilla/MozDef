#!/usr/bin/env bash
while true
do
          /opt/MozDef/cron/syncAlertsToMongo.py
          /opt/MozDef/cron/collectAttackers.py
          sleep 10
done
