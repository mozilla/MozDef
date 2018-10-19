ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PARENTDIR       := $(realpath ../)
STACK_NAME	:= mozdef-aws-nested
# MozDef uses a nested CF stack, the mozdef-parent.yml will tie all child stacks together and load them from S3
S3_BUCKET_NAME  := cf
S3_BUCKET_URI	:= s3://mozdef.infosec.mozilla.org/$(S3_BUCKET_NAME)
S3_STACK_URI	:= https://s3-us-west-2.amazonaws.com/mozdef.infosec.mozilla.org/cf/mozdef-parent.yml

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]\.PHONY.*].*:' Makefile
	@echo 'Run ./dmake <target> in order to run the Makefile targets in Docker'

# Note: This requires AWS access
.PHONY: packer-build
packer-build: ## Build the base AMI with packer
	cd packer && packer build packer.json

.PHONY: create-nested-stack create-s3-bucket
create-nested-stack: test ## Create everything you need for a fresh new stack!
	aws cloudformation create-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI)
create-s3-bucket:
	aws s3api create-bucket --bucket $(S3_BUCKET_NAME) --acl public-read

.PHONY: updated-nested-stack
update-nested-stack: test ## Updates the nested stack on AWS
	aws cloudformation update-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI)

.PHONY: cflint test
test: cflint
cflint: ## Verify the CloudFormation template pass linting tests
	-cfn-lint /opt/mozdef/cloudformation/*.yml

.PHONY: stack-status
stack-status: ## Output current CloudFormation stack status
	aws cloudformation describe-stacks --stack-name $(STACK_NAME)

.PHONY: upload-templates
upload-templates:
	aws s3 sync cloudformation/ $(S3_BUCKET_URI) --acl public-read
