#!/usr/bin/env bash
while true
do
          ../../cron/healthAndStatus.py
          ../../cron/healthToMongo.py
          sleep 15
done
