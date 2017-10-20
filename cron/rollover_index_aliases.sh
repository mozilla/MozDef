#!/bin/bash
# This is a temporary fix only

if ! [ -x "$(command -v curl)" ]; then
  exit 1
fi

alias_exists=`curl -s -XGET mozdef.private.scl3.mozilla.com:9200/_cat/aliases | grep "events\s"`
events_index=`curl -s -XGET mozdef.private.scl3.mozilla.com:9200/_cat/events | grep "events\s"`
rotate_alias=`curl -s -XGET mozdef.private.scl3.mozilla.com:9200/_cat/events | grep "events\s"`
index_current_date=`date +%Y%m%d`
index_new_date=$((index_current_date+1))
index_old_date=$((index_current_date-1))
successful_connect=`curl -s -XGET mozdef.private.scl3.mozilla.com:9200`

if [[ "${successful_connect}" == *"name"* ]]; then
  printf "We connected successfully with curl.\n"
else
  exit 1
fi

if [[ "${alias_exists}" == "events "* ]]; then
  printf "Event alias exists.\n"
else
  if [[ "${events_index}" == "events "* ]]; then
    exit 1
  fi
fi

printf "Rolling over events alias."
curl -XPOST mozdef.private.scl3.mozilla.com:9200/_aliases -d' { "actions": [{ "add" : { "index" : "events-'${index_new_date}'", "alias" : "events" } }, { "remove" : { "index" : "events-'${index_current_date}'", "alias" : "events" } } ]}'

printf "Rolling over events-previous alias."
curl -XPOST mozdef.private.scl3.mozilla.com:9200/_aliases -d' { "actions": [{ "add" : { "index" : "events-'${index_current_date}'", "alias" : "events-previous" } }, { "remove" : { "index" : "events-'${index_old_date}'", "alias" : "events-previous" } }, { "remove" : { "index" : "events-'${index_old_date}'", "alias" : "events-previous" } } ]}'
