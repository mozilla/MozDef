# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#

# usage:
# make single-build - build new single image from Dockerfile
# make single-build-no-cache - build new single image from Dockerfile from scratch
# make single-debug - debug run already created image by tag
# make single-run - run a single instance of MozDef
# make single-stop - stop a single instance of MozDef
# make single-rebuild - build, stop and run a new single instance of MozDef
# make multiple-build - build new mozdef environment in multiple containers
# make multiple-build-tests - build new mozdef environment for tests in multiple containers
# make multiple-build-no-cache - build new mozdef environment in multiple containers from scratch
# make multiple-run - run new mozdef environment in multiple containers
# make multiple-run-tests - run new mozdef environment for tests in multiple containers
# make multiple-stop - stop new mozdef environment in multiple containers
# make multiple-stop-tests - stop new mozdef environment for tests in multiple containers
# make multiple-rm - stop new mozdef environment in multiple containers and deattach volumes
# make multiple-rm-tests - stop new mozdef tests environment in multiple containers and deattach volumes
# make multiple-rebuild - build, stop and run new mozdef environment in multiple containers
# make multiple-rebuild-new - build, stop/rm and run new mozdef environment in multiple containers
# make multiple-rebuild-tests - build, stop/rm and run new mozdef environment for tests in multiple containers
# make multiple-rebuild-tests-new - build, stop/rm and run new mozdef environment for tests in multiple containers

NAME=mozdef
VERSION=0.1


single-build:
	docker build -f docker/Dockerfile -t $(NAME):$(VERSION) .

single-build-no-cache:
	docker build -f docker/Dockerfile --no-cache -t $(NAME):$(VERSION) .

single-run:
	docker run \
		-e TZ=UTC \
		-p 80:80 \
		-p 9090:9090 \
		-p 8080:8080 \
		-p 8081:8081 \
		-p 9200:9200 \
		-p 5672:5672 \
		-v mozdef-elasticsearch:/var/lib/elasticsearch \
		-v mozdef-mongodb:/var/lib/mongo \
		-v mozdef-rabbitmq:/var/lib/rabbitmq \
		-v mozdef-data:/opt/mozdef/envs/mozdef/data \
		-h $(NAME) --name $(NAME) -d $(NAME):$(VERSION)

single-debug:build
	docker run \
		-e TZ=UTC \
		-p 80:80 \
		-p 9090:9090 \
		-p 8080:8080 \
		-p 8081:8081 \
		-p 3002:3002 \
		-p 5672:5672 \
		-p 15672:15672 \
		-p 9200:9200 \
		-v mozdef-elasticsearch:/var/lib/elasticsearch \
		-v mozdef-mongodb:/var/lib/mongo \
		-v mozdef-rabbitmq:/var/lib/rabbitmq \
		-v mozdef-data:/opt/mozdef/envs/mozdef/data \
		-h $(NAME) -t -i $(NAME):$(VERSION) /bin/bash

single-stop:
	-docker rm -f $(NAME)

single-rebuild: single-build single-stop single-run

.PHONY: single-build single-build-no-cache single-run single-debug single-stop single-rebuild

multiple-run:
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) up -d

multiple-run-tests:
	docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) up -d --remove-orphans

multiple-build:
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) build

multiple-build-tests:
	docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) build

multiple-build-no-cache:
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) build --no-cache

multiple-stop:
	-docker-compose -f docker/compose/docker-compose.yml -p $(NAME) stop

multiple-stop-tests:
	-docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) stop

multiple-rm:
	-docker-compose -f docker/compose/docker-compose.yml -p $(NAME) down -v --remove-orphans

multiple-rm-tests:
	-docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) down -v --remove-orphans

multiple-rebuild: multiple-build multiple-stop multiple-run

multiple-rebuild-new: multiple-build multiple-rm multiple-run

multiple-rebuild-tests: multiple-build-tests multiple-stop-tests multiple-run-tests

multiple-rebuild-tests-new: multiple-build-tests multiple-rm-tests multiple-run-tests

.PHONY: multiple-build multiple-run multiple-stop multiple-rebuild
