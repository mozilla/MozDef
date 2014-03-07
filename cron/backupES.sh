#!/bin/bash
# herein we backup our indexes! this script should run at like 6pm or something, after logstash
# rotates to a new ES index and theres no new data coming in to the old one. we grab metadatas,
# compress the data files, create a restore script, and push it all up to S3.

#set environment for s3/python
source  /home/mozdef/envs/mozdef/bin/activate
#figure out what we are archiving (default to yesterday's events-YYYYMMDD index)
IDATE=`date --date='yesterday' +"%Y%m%d"`
INDEXNAME="events-$IDATE" # this had better match the index name in ES
#maybe we were told what to archive.
if [[ ! -z $1 ]]
then
    INDEXNAME=$1
fi

#compensate for qa server pathname strangeness.
HOSTNAME=`hostname`
if [[ $HOSTNAME == *mozdefqa* ]]
then
    INDEXDIR="/data/es/mozdefqa/nodes/0/indices/"
else
    INDEXDIR="/data/es/mozdef/nodes/0/indices/"
fi
BACKUPCMD="/home/mozdef/envs/mozdef/bin/s3cmd put"
echo "using $INDEXDIR as index directory"
echo "archiving $INDEXNAME"

BACKUPDIR="/tmp/es-backups/"
YEARMONTH=`date --date='yesterday' +"%Y-%m"`
S3TARGET="s3://mozdefesbackups/elasticsearch/$YEARMONTH/$HOSTNAME/$INDEXNAME"

# create mapping file with index settings. this metadata is required by ES to use index file data
echo -n "Backing up metadata... "
curl -XGET -o /tmp/mapping "http://localhost:9200/$INDEXNAME/_mapping?pretty=true" > /dev/null 2>&1
sed -i '1,2d' /tmp/mapping #strip the first two lines of the metadata
echo '{"settings":{"number_of_shards":5,"number_of_replicas":1},"mappings":{' >> /tmp/mappost 
# prepend hardcoded settings metadata to index-specific metadata
cat /tmp/mapping >> /tmp/mappost
echo "DONE!"

# now lets tar up our data files. these are huge, so lets be nice
echo -n "Backing up data files (this may take some time)... "
mkdir -p $BACKUPDIR
cd $INDEXDIR
nice -n 19 tar czf $BACKUPDIR/$INDEXNAME.tar.gz $INDEXNAME 
echo "DONE!"

echo -n "Creating restore script... "
# time to create our restore script! oh god scripts creating scripts, this never ends well...
cat << EOF >> $BACKUPDIR/$INDEXNAME-restore.sh
#!/bin/bash
# this script requires $INDEXNAME.tar.gz and will restore it into elasticsearch
# it is ESSENTIAL that the index you are restoring does NOT exist in ES. delete it
# if it does BEFORE trying to restore data.

# create index and mapping
echo -n "Creating index and mappings... "
curl -XPUT 'http://localhost:9200/$INDEXNAME/' -d '`cat /tmp/mappost`' > /dev/null 2>&1
echo "DONE!"

# extract our data files into place
echo -n "Restoring index (this may take a while)... "
cd $INDEXDIR
tar xzf $BACKUPDIR/$INDEXNAME.tar.gz
echo "DONE!"

# restart ES to allow it to open the new dir and file data
echo -n "Restarting Elasticsearch... "
/etc/init.d/elasticsearch restart
echo "DONE!"
EOF
echo "DONE!" # restore script done

# push both tar.gz and restore script to s3
echo -n "Saving to S3 (this may take some time)... "
$BACKUPCMD $BACKUPDIR/$INDEXNAME.tar.gz $S3TARGET.tar.gz
$BACKUPCMD $BACKUPDIR/$INDEXNAME-restore.sh $S3TARGET-restore.sh
echo "DONE!"

# cleanup tmp files
rm /tmp/mappost
rm /tmp/mapping
