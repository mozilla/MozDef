#!/usr/bin/env bash
while true
do
          ~/MozDef/cron/syncAlertsToMongo.py
          ~/MozDef/cron/collectAttackers.py
          sleep 10
done
