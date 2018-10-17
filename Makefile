# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#

ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
DKR_IMAGES	:= mozdef_alertplugins mozdef_alerts mozdef_base mozdef_bootstrap mozdef_meteor mozdef_rest \
		   mozdef_mq_eventtask mozdef_loginput mozdef_cron mozdef_elasticsearch mozdef_mongodb \
		   mozdef_syslog mozdef_nginx mozdef_tester mozdef_rabbitmq mozdef_kibana
NAME		:= mozdef
VERSION		:= 0.1
NO_CACHE	:= #--no-cache
GITHASH		:= $(shell git rev-parse --short HEAD)

.PHONY:all
all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]^\.PHONY.*].*:' Makefile

.PHONY: run runbonly
run: build ## Run all MozDef containers
	docker-compose -f docker/compose/docker-compose-rebuild.yml -f docker/compose/docker-compose.yml -p $(NAME) up -d

runonly:
	docker-compose -f docker/compose/docker-compose-rebuild.yml -f docker/compose/docker-compose.yml -p $(NAME) up -d

.PHONY: run-norebuild
run-norebuild: nobuild ## Run all MozDef containers from pre-built images
	docker-compose -f docker/compose/docker-compose-norebuild.yml -f docker/compose/docker-compose.yml -p $(NAME) up -d

.PHONY: run-cloudy-mozdef
run-cloudy-mozdef: ## Run the MozDef containers necessary to run in AWS (`cloudy-mozdef`). This is used by the CloudFormation-initiated setup.
	docker-compose -f docker/compose/docker-compose-cloudy-mozdef.yml -p $(NAME) up -d

# TODO? add custom test targets for individual tests (what used to be `multiple-tests` for example
# The docker files are still in docker/compose/docker*test*
.PHONY: test tests run-tests run-fast-tests test-fast
test: build-tests run-tests ## Running tests from locally-built images
tests: build-tests run-tests
test-fast: nobuild-tests run-fast-tests ## Running tests from pre-built images (hub.docker.com/mozdef
run-fast-tests:
	docker-compose -f tests/docker-compose-norebuild.yml -f tests/docker-compose.yml -p $(NAME) up -d
	@echo "Waiting for the instance to come up..."
	sleep 10
	@echo "Running flake8.."
	docker run -it mozdef/mozdef_tester bash -c "source /opt/mozdef/envs/python/bin/activate && flake8 --config .flake8 ./"
	@echo "Running py.test..."
	docker run -it --network=mozdef_default mozdef/mozdef_tester bash -c "source /opt/mozdef/envs/python/bin/activate && py.test --delete_indexes --delete_queues tests"

run-tests:
	docker-compose -f tests/docker-compose-rebuild.yml -f tests/docker-compose.yml -p $(NAME) up -d
	@echo "Waiting for the instance to come up..."
	sleep 10
	@echo "Running flake8.."
	docker run -it mozdef_tester bash -c "source /opt/mozdef/envs/python/bin/activate && flake8 --config .flake8 ./"
	@echo "Running py.test..."
	docker run -it --network=mozdef_default mozdef_tester bash -c "source /opt/mozdef/envs/python/bin/activate && py.test --delete_indexes --delete_queues tests"

.PHONY: build
build:  ## Build local MozDef images (use make NO_CACHE=--no-cache build to disable caching)
	docker-compose -f docker/compose/docker-compose-rebuild.yml -f docker/compose/docker-compose.yml -p $(NAME) $(NO_CACHE) build

.PHONY: nobuild
nobuild:
	docker-compose -f docker/compose/docker-compose-norebuild.yml -f docker/compose/docker-compose.yml -p $(NAME) $(NO_CACHE) build

.PHONY: build-tests nobuild-tests
build-tests:
	docker-compose -f tests/docker-compose-rebuild.yml -f tests/docker-compose.yml -p $(NAME) $(NO_CACHE) build

nobuild-tests:
	docker-compose -f tests/docker-compose-norebuild.yml -f tests/docker-compose.yml -p $(NAME) $(NO_CACHE) build

.PHONY: stop down
stop: down
down: ## Shutdown all services we started with docker-compose
	docker-compose -f docker/compose/docker-compose-rebuild.yml -f docker/compose/docker-compose.yml -p $(NAME) stop

.PHONY: docker-push docker-get hub hub-get
docker-push: hub
hub: ## Upload locally built MozDef images tagged as the current git head (hub.docker.com/mozdef). Use make GITHASH=latest to tag latest.
	docker login
	@echo "Tagging current docker images with git HEAD shorthash..."
	$(foreach var,$(DKR_IMAGES),docker tag $(var):latest mozdef/$(var):$(GITHASH);)
	@echo "Uploading images to docker..."
	$(foreach var,$(DKR_IMAGES),docker push mozdef/$(var):$(GITHASH);)

docker-get: hub-get
hub-get: ## Download all pre-built images (hub.docker.com/mozdef)
	$(foreach var,$(DKR_IMAGES),docker pull mozdef/$(var):$(GITHASH);)

.PHONY: clean
clean: ## Cleanup all docker volumes and shutdown all related services
	-docker-compose -f docker/compose/docker-compose-rebuild.yml -f docker/compose/docker-compose.yml -p $(NAME) down -v --remove-orphans
# Shorthands
.PHONY: rebuild
rebuild: clean build
