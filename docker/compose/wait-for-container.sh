#!/bin/bash

set -e

host="$1"
shift
cmd=("$@")

while ping $host -c 1 > /dev/null 2>&1
do
  >&2 echo "$host container is still running...sleeping 2 seconds"
  sleep 2
done

>&2 echo "$host container is finished...starting container"
exec "${cmd[@]}"