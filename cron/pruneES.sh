#!/bin/bash

#figure out what we are archiving (events-YYYYMMDD index)
IDATE=`date --date='10 days ago' +"%Y%m%d"`
INDEXNAME="events-$IDATE" # this had better match the index name in ES
#maybe we were told what to archive.
if [[ ! -z $1 ]]
then
    INDEXNAME=$1
fi

HOSTNAME=`hostname`
echo "Deleting index http://$HOSTNAME:9200/$INDEXNAME/"
curl -XDELETE "http://$HOSTNAME:9200/$INDEXNAME/"
echo "DONE"
