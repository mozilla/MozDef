ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
IMAGE_NAME	:= mozdef-deployment
S3_INFOSEC_URI	:= s3://mozdef.infosec.mozilla.org/cf
S3_STACK_URI	:= https://s3-us-west-2.amazonaws.com/cf/nested-stack.yml
PARENTDIR   := $(realpath ../)

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]].*:' Makefile

docker-build:
	docker build -t $(IMAGE_NAME):latest .

deploy-shell:
	docker run -ti -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef -v $(PARENTDIR):/opt/gitrepo $(IMAGE_NAME):latest /bin/bash

packer-build:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "cd packer && packer build packer.json"

deploy-nested-cloudformation:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "ansible-playbook -c local ansible/update-ami-metadata.yml"
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "aws s3 sync /opt/mozdef/ansible/files/stacks/ $(S3_INFOSEC_URI) --acl public-read"

test-nested-stack:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "ansible-playbook -c local ansible/update-ami-metadata.yml"
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "aws s3 sync /opt/mozdef/ansible/files/stacks/ $(S3_INFOSEC_URI) --acl public-read"
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "aws s3 cp /opt/mozdef/cloudformation/nested-stack.yml $(S3_INFOSEC_URI)/nested-stack.yml --acl public-read"
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "aws cloudformation update-stack --stack-name mozdef-nested --template-url $(S3_STACK_URI)"

stack-status:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef $(IMAGE_NAME):latest bash -c "aws cloudformation describe-stacks --stack-name mozdef-nested"
