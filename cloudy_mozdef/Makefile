ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PARENTDIR       := $(realpath ../)
IMAGE_NAME	:= mozdef-deployment
S3_INFOSEC_URI	:= s3://mozdef.infosec.mozilla.org/cf
S3_STACK_URI	:= https://s3-us-west-2.amazonaws.com/cf/nested-stack.yml
DOCKER_BASH_RUN	:= docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest /bin/bash -c

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]\.PHONY.*].*:' Makefile

.PHONY: build docker-build
build: docker-build packer-build
docker-build: ## Build the docker image that is used for deployment of CloudFormation templates
	docker build -t $(IMAGE_NAME):latest .

.PHONY: docker-shell
deploy-shell: ## Spawn a shell for hacking into the docker image
	docker run -ti -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef -v $(PARENTDIR):/opt/gitrepo $(IMAGE_NAME):latest /bin/bash

# Note: This requires AWS access
.PHONY: packer-build
packer-build: docker-build ## Build the base AMI with packer
	$(DOCKER_BASH_RUN) "cd packer && packer build packer.json"

.PHONY: deploy-nested-cloudformation
deploy-nested-cloudformation: cflint ## Deploy our nested ClouFormation stack
	$(DOCKER_BASH_RUN) "ansible-playbook -c local ansible/update-ami-metadata.yml"
	$(DOCKER_BASH_RUN) "aws s3 sync /opt/mozdef/ansible/files/stacks/ $(S3_INFOSEC_URI) --acl public-read"

.PHONY: test
test: cflint test-nested-stack

.PHONY: test-nested-stack cflint
test-nested-stack:
	$(DOCKER_BASH_RUN) "ansible-playbook -c local ansible/update-ami-metadata.yml"
	$(DOCKER_BASH_RUN) "aws s3 sync /opt/mozdef/ansible/files/stacks/ $(S3_INFOSEC_URI) --acl public-read"
	$(DOCKER_BASH_RUN) "aws s3 cp /opt/mozdef/cloudformation/nested-stack.yml $(S3_INFOSEC_URI)/nested-stack.yml --acl public-read"
	$(DOCKER_BASH_RUN) "aws cloudformation update-stack --stack-name mozdef-nested --template-url $(S3_STACK_URI)"

.PHONY: cflint
cflint: ## Verify the CloudFormation template pass linting tests
	$(DOCKER_BASH_RUN) "cfn-lint cloudformation/*.yml"

.PHONY: stack-status
stack-status: ## Output current CloudFormation stack status
	$(DOCKER_BASH_RUN) "aws cloudformation describe-stacks --stack-name mozdef-nested"

.PHONY: upload-templates
upload-templates: ## Upload all AWS CloudFormation templates in the cloudformation/ directory to S3
	$(foreach var,$(wildcard cloudformation/*.yml),aws s3 cp $(var) $(S3_INFOSEC_URI) --acl public-read;)
