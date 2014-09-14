# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Yohann Lepage yohann@lepage.info
# Anthony Verez averez@mozilla.com

# Project: MozDef
# Author: 2xyo <yohann@lepage.info>
# Date: 2014
# usage:
#	make build	- build new image from Dockerfile
#	make debug	- debug run already created image by tag
#	make try	- build and run in debug mode

NAME=mozdef
VERSION=0.1


build:
	docker build -t $(NAME):$(VERSION) .

build-no-cache:
	docker build --no-cache -t $(NAME):$(VERSION) .

run:
	docker run -p 3000:3000 -p 9090:9090 -p 9200:9200 -p 8080:8080 -p 8081:8081 \
		-h $(NAME) -t -i $(NAME):$(VERSION)

debug:build
	docker run -p 3000:3000 -p 9090:9090 -p 9200:9200 -p 8080:8080 -p 8081:8081 \
		-v $(shell pwd)/container/var/lib/elasticsearch:/var/lib/elasticsearch \
		-v $(shell pwd)/container/var/log/elasticsearch:/var/log/elasticsearch \
		-v $(shell pwd)/container/var/lib/mongodb:/var/lib/mongodb \
		-v $(shell pwd)/container/var/log/mongodb:/var/log/mongodb \
		-v $(shell pwd)/container/var/log/nginx:/var/log/nginx \
		-v $(shell pwd)/container/var/log/mozdef:/var/log/mozdef \
	 	-h $(NAME) -t -i $(NAME):$(VERSION) /bin/bash


try: build run


.PHONY: build debug run
