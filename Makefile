# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#

# usage:
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

ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
NAME=mozdef
VERSION=0.1

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]].*:' Makefile

run: build
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) up -d

run-tests: build-tests
	docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) up -d --remove-orphans

build:
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) build

build-tests:
	docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) build

build-no-cache:
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) build --no-cache

stop:
down:
	-docker-compose -f docker/compose/docker-compose.yml -p $(NAME) stop

stop-tests:
down-tests:
	-docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) stop

rm:
	-docker-compose -f docker/compose/docker-compose.yml -p $(NAME) down -v --remove-orphans

rm-tests:
	-docker-compose -f docker/compose/docker-compose-tests.yml -p $(NAME) down -v --remove-orphans

# Shorthands
rebuild: multiple-build multiple-stop multiple-run

rebuild-tests: multiple-build-tests multiple-stop-tests multiple-run-tests


.PHONY: build build-tests rebuild rebuild-tests run run-tests stop down clean
