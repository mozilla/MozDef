#!/bin/bash
# herein we backup our indexes! this script should run at like 6pm or something, after you
# rotate indexes to a new ES date index and theres no new data coming in to the old one. we create a snapshot,
# create a restore script, and push it all up to S3.

# Usage: ./backupES10.sh <esserverhostname> [index]

#set environment for s3/python
source /home/mozdef/envs/mozdef/bin/activate
#figure out what we are archiving (default to yesterday's events-YYYYMMDD index)
IDATE=`date --date='yesterday' +"%Y%m%d"`
INDEXNAME="events-$IDATE" # this had better match the index name in ES
#maybe we were told what to archive.
HOSTNAME=`hostname`
if [[ ! -z $1 ]]
then
    HOSTNAME=$1
fi
if [[ ! -z $2 ]]
then
    INDEXNAME=$2
fi

BACKUPCMD="/home/mozdef/envs/mozdef/bin/s3cmd put"

#compensate for qa server pathname strangeness.
YEARMONTH=`date --date='yesterday' +"%Y-%m"`
S3TARGET="s3://mozdefesbackups/elasticsearch/$YEARMONTH/$HOSTNAME/$INDEXNAME"

# if snapshot repo not registered
if result=$(curl -s -XGET "http://${HOSTNAME}:9200/_snapshot/s3backup?pretty" | grep "\"status\" : 404"); then
    echo "Configuring snapshot repository (first time run only)..."
    curl -s -XPUT "http://${HOSTNAME}:9200/_snapshot/s3backup" -d '{
        "type": "s3",
        "settings": {
            "bucket": "mozdefesbackups",
            "base_path": "elasticsearch/'"$YEARMONTH"'/'"$HOSTNAME"'",
            "region": "us-west"
        }
    }' > /dev/null 2>&1
    echo "DONE"
fi

echo -n "Creating snapshot (this may take a while)..."
curl -s -XPUT "http://${HOSTNAME}:9200/_snapshot/s3backup/$INDEXNAME?wait_for_completion=true" -d '{
"indices": "'"${INDEXNAME}"'"
}' > /dev/null 2>&1
echo "DONE"

echo -n "Creating restore script... "
# time to create our restore script! oh god scripts creating scripts, this never ends well...
cat << EOF >> ~/$INDEXNAME-restore.sh
#!/bin/bash

echo -n "Restoring the snapshot..."
curl -s -XPOST "http://${HOSTNAME}:9200/_snapshot/s3backup/${INDEXNAME}/_restore?wait_for_completion=true"

echo "DONE!"
EOF
echo "DONE!" # restore script done

# push the restore script to s3
echo -n "Saving to restore script to S3... "
$BACKUPCMD ~/$INDEXNAME-restore.sh $S3TARGET-restore.sh > /dev/null 2>&1
echo "DONE!"

# cleanup tmp files
echo -n "Cleaning up files..."
rm -rf ~/$INDEXNAME-restore.sh
echo "DONE!"
