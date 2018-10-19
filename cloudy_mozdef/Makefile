ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PARENTDIR       := $(realpath ../)
AWS_REGION	:= us-west-2
STACK_NAME	:= mozdef-aws-nested
STACK_PARAMS	:= file://aws_parameters.json
# MozDef uses a nested CF stack, the mozdef-parent.yml will tie all child stacks together and load them from S3
# See also mozdef.infosec.mozilla.org bucket
S3_BUCKET_NAME  := mozdef.infosec.allizom.org
S3_BUCKET_PATH	:= cf
S3_BUCKET_URI	:= s3://$(S3_BUCKET_NAME)/$(S3_BUCKET_PATH)
S3_STACK_URI	:= https://s3-$(AWS_REGION).amazonaws.com/$(S3_BUCKET_NAME)/$(S3_BUCKET_PATH)/mozdef-parent.yml

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]\.PHONY.*].*:' Makefile
	@echo 'Run ./dmake <target> in order to run the Makefile targets in Docker'

# Note: This requires AWS access
.PHONY: packer-build
packer-build: ## Build the base AMI with packer
	cd packer && packer build packer.json

.PHONY: create-stack
create-stack: test ## Create everything you need for a fresh new stack!
	@export AWS_REGION=$(AWS_REGION)
	@echo "Make sure you have a param file ($(STACK_PARAMS)) with OIDCClientSecret set."
	aws cloudformation create-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI) \
	  --capabilities CAPABILITY_IAM \
	  --parameters $(STACK_PARAMS)

.PHONY: create-s3-bucket
create-s3-bucket:
	@export AWS_REGION=$(AWS_REGION)
	aws s3api create-bucket --bucket $(S3_BUCKET_NAME) --acl public-read --create-bucket-configuration LocationConstraint=$(AWS_REGION)

.PHONY: updated-nested-stack
update-stack: test ## Updates the nested stack on AWS
	@export AWS_REGION=$(AWS_REGION)
	aws cloudformation update-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI) \
	  --capabilities CAPABILITY_IAM \
	  --parameters $(STACK_PARAMS)

.PHONY: cflint test
test: cflint
cflint: ## Verify the CloudFormation template pass linting tests
	-cfn-lint /opt/mozdef/cloudformation/*.yml

.PHONY: stack-status
stack-status: ## Output current CloudFormation stack status
	@export AWS_REGION=$(AWS_REGION)
	watch -g aws cloudformation describe-stacks --stack-name $(STACK_NAME)

.PHONY: upload-templates
upload-templates:
	@export AWS_REGION=$(AWS_REGION)
	aws s3 sync cloudformation/ $(S3_BUCKET_URI) --acl public-read
