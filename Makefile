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
NAME		:= mozdef
VERSION		:= 0.1
NO_CACHE	:= #--no-cache

.PHONY:all
all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]^\.PHONY.*].*:' Makefile

.PHONY: build
run: build
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) up -d

# TODO? add custom test targets for individual tests (what used to be `multiple-tests` for example
# The docker files are still in docker/compose/docker*test*
.PHONY: test tests run-tests
test: run-tests
tests: run-tests
run-tests: build-tests
	docker-compose -f tests/docker-compose.yml -p $(NAME) up -d
	@echo "Waiting for the instance to come up..."
	sleep 10
	@echo "Running flake8.."
	docker run -it mozdef_tester bash -c "source /opt/mozdef/envs/python/bin/activate && flake8 --config .flake8 ./"
	@echo "Running py.test..."
	docker run -it --network=mozdef_default mozdef_tester bash -c "source /opt/mozdef/envs/python/bin/activate && py.test --delete_indexes --delete_queues tests"

.PHONY: build
build:
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) $(NO_CACHE) build

.PHONY: build-tests
build-tests:
	docker-compose -f tests/docker-compose.yml -p $(NAME) $(NO_CACHE) build

.PHONY: stop down
stop: down
down:
	docker-compose -f docker/compose/docker-compose.yml -p $(NAME) stop

.PHONY: clean
clean:
	-docker-compose -f docker/compose/docker-compose.yml -p $(NAME) down -v --remove-orphans

# Shorthands
.PHONY: rebuild
rebuild: rm build
