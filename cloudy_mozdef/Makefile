ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PARENTDIR       := $(realpath ../)
AWS_REGION	:= us-west-2
STACK_NAME	:= mozdef-aws-nested
STACK_PARAMS_FILENAME	:= aws_parameters.json
# For more information on the rationale behind the code in STACK_PARAMS see https://github.com/aws/aws-cli/issues/2429#issuecomment-441133480
STACK_PARAMS	:= $(shell test -e $(STACK_PARAMS_FILENAME) && python -c 'import json,sys;f=open(sys.argv[1]);print(" ".join([",".join(["%s=\\\"%s\\\""%(k,v) for k,v in x.items()]) for x in json.load(f)]));f.close()' $(STACK_PARAMS_FILENAME))
# MozDef uses a nested CF stack, the mozdef-parent.yml will tie all child stacks together and load them from S3
# See also mozdef.infosec.mozilla.org bucket
S3_BUCKET_NAME	:= mozdef.infosec.allizom.org
S3_BUCKET_PATH	:= cf
S3_BUCKET_URI	:= s3://$(S3_BUCKET_NAME)/$(S3_BUCKET_PATH)
# Location to publish templates for public consumption
S3_PUBLISHED_BUCKET_NAME	:= public.us-west-2.infosec.mozilla.org
S3_PUBLISHED_BUCKET_PATH	:= mozdef/cf
S3_PUBLISHED_BUCKET_URI	:= s3://$(S3_PUBLISHED_BUCKET_NAME)/$(S3_PUBLISHED_BUCKET_PATH)

S3_STACK_URI	:= https://s3-$(AWS_REGION).amazonaws.com/$(S3_BUCKET_NAME)/$(S3_BUCKET_PATH)/
# OIDC_CLIENT_SECRET is set in an environment variable by running "source aws_parameters.sh"
OIDC_CLIENT_SECRET_PARAM_ARG := $(shell test -n "$(OIDC_CLIENT_SECRET)" && echo "ParameterKey=OIDCClientSecret,ParameterValue=$(OIDC_CLIENT_SECRET)")

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
	@echo "Make sure you have an environment variable OIDC_CLIENT_SECRET set."
	aws cloudformation create-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI)mozdef-parent.yml \
	  --capabilities CAPABILITY_IAM \
	  --parameters ParameterKey=S3TemplateLocation,ParameterValue=$(S3_STACK_URI) \
	               $(OIDC_CLIENT_SECRET_PARAM_ARG) \
	               $(STACK_PARAMS) \
	  --output text

.PHONY: create-s3-bucket
create-s3-bucket:
	@export AWS_REGION=$(AWS_REGION)
	aws s3api create-bucket --bucket $(S3_BUCKET_NAME) --acl public-read --create-bucket-configuration LocationConstraint=$(AWS_REGION)

.PHONY: updated-nested-stack
update-stack: test ## Updates the nested stack on AWS
	@export AWS_REGION=$(AWS_REGION)
	aws cloudformation update-stack --stack-name $(STACK_NAME) --template-url $(S3_STACK_URI)mozdef-parent.yml \
	  --capabilities CAPABILITY_IAM \
	  --parameters ParameterKey=S3TemplateLocation,ParameterValue=$(S3_STACK_URI) \
	               $(OIDC_CLIENT_SECRET_PARAM_ARG) \
	  --output text

# --ignore-checks=E2502 : https://github.com/awslabs/cfn-python-lint/issues/408
.PHONY: cflint test
test: cflint
cflint: ## Verify the CloudFormation template pass linting tests
	-cfn-lint --ignore-checks=E2502 cloudformation/*.yml

.PHONY: stack-status
stack-status: ## Output current CloudFormation stack status
	@export AWS_REGION=$(AWS_REGION)
	watch -g aws cloudformation describe-stacks --stack-name $(STACK_NAME)

.PHONY: upload-templates
upload-templates:
	@export AWS_REGION=$(AWS_REGION)
	aws s3 sync cloudformation/ $(S3_BUCKET_URI) --acl public-read --exclude="*" --include="*.yml"

.PHONY: publish-templates
publish-templates:
	@export AWS_REGION=$(AWS_REGION)
	aws s3 sync cloudformation/ $(S3_PUBLISHED_BUCKET_URI) --exclude="*" --include="*.yml"
