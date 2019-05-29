#!/bin/bash

set -e

hostport=(${1//:/ })
host=${hostport[0]}
port=${hostport[1]}
shift
cmd=("$@")

until (echo > /dev/tcp/$host/$port) >/dev/null 2>&1
do
  >&2 echo "$host:$port is still not ready yet...sleeping 2 seconds"
  sleep 2
done

>&2 echo "$host:$port is ready...starting container"
exec "${cmd[@]}"