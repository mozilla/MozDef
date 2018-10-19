ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PARENTDIR       := $(realpath ../)
IMAGE_NAME	:= mozdef-deployment
STACK_NAME	:= mozdef-aws-nested
# MozDef uses a nested CF stack, the mozdef-parent.yml will tie all child stacks together and load them from S3
S3_BUCKET_URI	:= s3://mozdef.infosec.mozilla.org/cf
S3_STACK_URI	:= https://s3-us-west-2.amazonaws.com/mozdef.infosec.mozilla.org/cf/mozdef-parent.yml
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

.PHONY: create-nested-stack create-s3-bucket
create-nested-stack: upload-templates test ## Create everything you need for a fresh new stack!
	$(DOCKER_BASH_RUN) "aws cloudformation create-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI)"
create-s3-bucket:
	$(DOCKER_BASH_RUN) "aws s3api create-bucket --bucket $(S3_BUCKET_URI) --acl public-read"

.PHONY: updated-nested-stack
update-nested-stack: upload-templates test ## Updates the nested stack on AWS
	$(DOCKER_BASH_RUN) "aws cloudformation update-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI)"

.PHONY: cflint test
test: cflint
cflint: ## Verify the CloudFormation template pass linting tests
	-$(DOCKER_BASH_RUN) "cfn-lint /opt/mozdef/cloudformation/*.yml"

.PHONY: stack-status
stack-status: ## Output current CloudFormation stack status
	$(DOCKER_BASH_RUN) "aws cloudformation describe-stacks --stack-name $(STACK_NAME)"

.PHONY: upload-templates
upload-templates:
	$(DOCKER_BASH_RUN) "aws s3 sync /opt/mozdef/cloudformation/ $(S3_BUCKET_URI) --acl public-read"
