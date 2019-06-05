ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PARENTDIR       := $(realpath ../)
AWS_REGION	:= us-west-2
STACK_NAME	:= mozdef-aws-nested
BRANCH := master
AMI_MAP_TEMP_FILE	:= /tmp/mozdef-ami-map.txt
DEV_STACK_PARAMS_FILENAME	:= aws_parameters.dev.json
# For more information on the rationale behind the code in STACK_PARAMS see https://github.com/aws/aws-cli/issues/2429#issuecomment-441133480
DEV_STACK_PARAMS	:= $(shell test -e $(DEV_STACK_PARAMS_FILENAME) && python -c 'import json,sys;f=open(sys.argv[1]);print(" ".join([",".join(["%s=\\\"%s\\\""%(k,v) for k,v in x.items()]) for x in json.load(f)]));f.close()' $(DEV_STACK_PARAMS_FILENAME))
OIDC_CLIENT_ID		:= $(shell test -e $(DEV_STACK_PARAMS_FILENAME) && python -c 'import json,sys;f=open(sys.argv[1]);print(next((x["ParameterValue"] for x in json.load(f) if x["ParameterKey"]=="OIDCClientId"),""));f.close()' $(DEV_STACK_PARAMS_FILENAME))
DOMAIN_NAME			:= $(shell test -e $(DEV_STACK_PARAMS_FILENAME) && python -c 'import json,sys;f=open(sys.argv[1]);print(next((x["ParameterValue"] for x in json.load(f) if x["ParameterKey"]=="DomainName"),""));f.close()' $(DEV_STACK_PARAMS_FILENAME))
# MozDef uses a nested CF stack, the mozdef-parent.yml will tie all child stacks together and load them from S3
# See also mozdef.infosec.mozilla.org bucket
S3_DEV_BUCKET_NAME	:= mozdef.infosec.allizom.org
S3_DEV_BUCKET_PATH	:= cf
S3_DEV_BUCKET_URI	:= s3://$(S3_DEV_BUCKET_NAME)/$(S3_DEV_BUCKET_PATH)
S3_DEV_STACK_URI	:= https://s3-$(AWS_REGION).amazonaws.com/$(S3_DEV_BUCKET_NAME)/$(S3_DEV_BUCKET_PATH)/
# Location to publish templates for public consumption
S3_PROD_BUCKET_NAME	:= public.us-west-2.infosec.mozilla.org
S3_PROD_BUCKET_PATH	:= mozdef/cf
S3_PROD_BUCKET_URI	:= s3://$(S3_PROD_BUCKET_NAME)/$(S3_PROD_BUCKET_PATH)
S3_PROD_STACK_URI	:= https://s3-$(AWS_REGION).amazonaws.com/$(S3_PROD_BUCKET_NAME)/$(S3_PROD_BUCKET_PATH)/

# OIDC_CLIENT_SECRET and other secrets are set in an environment variable by running "source aws_parameters.sh"
OIDC_CLIENT_SECRET_PARAM_ARG := $(shell test -n "$(OIDC_CLIENT_SECRET)" && echo "ParameterKey=OIDCClientSecret,ParameterValue=$(OIDC_CLIENT_SECRET),UsePreviousValue=false")
ALB_BASIC_AUTH_SECRET_PARAM_ARG := $(shell test -n "$(ALB_BASIC_AUTH_SECRET)" && echo "ParameterKey=ALBBasicAuthSecret,ParameterValue=$(ALB_BASIC_AUTH_SECRET),UsePreviousValue=false")

# Make functions
eq = $(if $(or $(1),$(2)),$(and $(findstring $(1),$(2)),\
                              $(findstring $(2),$(1))),1)

.PHONY:all
all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]\.PHONY.*].*:' Makefile
	@echo 'Run ./dmake <target> in order to run the Makefile targets in Docker'

# Note: This requires AWS access
# https://blog.gruntwork.io/locating-aws-ami-owner-id-and-image-name-for-packer-builds-7616fe46b49a
.PHONY: packer-build-github
packer-build-github: ## Build the base AMI with packer
	@echo "Branch based build triggered for $(BRANCH)."
	ci/pack_and_copy $(BRANCH) $(AMI_MAP_TEMP_FILE)

.PHONY: safety-checks
safety-checks:
	@echo "Making sure you have an environment variable OIDC_CLIENT_SECRET set."
	@test -n "$(OIDC_CLIENT_SECRET_PARAM_ARG)" -a -n "$(OIDC_CLIENT_ID)" -o -z "$(OIDC_CLIENT_SECRET_PARAM_ARG)" -a -z "$(OIDC_CLIENT_ID)"
	@echo "Making sure you have either OIDC_CLIENT_ID or ALB_BASIC_AUTH_SECRET set."
	# If both are equal then you're either leaking the secret, or, most likely, both are equal to string ""
	# which is unsafe (as it would effectively give you a basic auth password of string "")
	$(call eq, $(OIDC_CLIENT_ID), $(ALB_BASIC_AUTH_SECRET_PARAM_ARG))

.PHONY: create-dev-stack
create-dev-stack: safety-checks test ## Create everything you need for a fresh new stack!
	@export AWS_REGION=$(AWS_REGION)
	aws cloudformation create-stack --stack-name $(STACK_NAME) --template-url $(S3_DEV_STACK_URI)mozdef-parent.yml \
	  --capabilities CAPABILITY_IAM \
	  --parameters $(OIDC_CLIENT_SECRET_PARAM_ARG) \
	               $(ALB_BASIC_AUTH_SECRET_PARAM_ARG) \
	               $(DEV_STACK_PARAMS) \
	  --output text

.PHONY: create-dev-s3-bucket
create-dev-s3-bucket:
	@export AWS_REGION=$(AWS_REGION)
	aws s3api create-bucket --bucket $(S3_DEV_BUCKET_NAME) --acl public-read --create-bucket-configuration LocationConstraint=$(AWS_REGION)

.PHONY: update-dev-stack
update-dev-stack: safety-checks test ## Updates the nested stack on AWS
	@export AWS_REGION=$(AWS_REGION)
	aws cloudformation update-stack --stack-name $(STACK_NAME) --template-url $(S3_DEV_STACK_URI)mozdef-parent.yml \
	  --capabilities CAPABILITY_IAM \
	  --parameters $(OIDC_CLIENT_SECRET_PARAM_ARG) \
	               $(ALB_BASIC_AUTH_SECRET_PARAM_ARG) \
	               $(DEV_STACK_PARAMS) \
	  --output text

.PHONY: test
test: cfn-lint

.PHONY: cfn-lint
cfn-lint: ## Verify the CloudFormation template pass linting tests
	-cfn-lint cloudformation/*.yml

.PHONY: stack-status
stack-status: ## Output current CloudFormation stack status
	@export AWS_REGION=$(AWS_REGION)
	watch -g aws cloudformation describe-stacks --stack-name $(STACK_NAME)

.PHONY: publish-dev-templates
publish-dev-templates:
	@export AWS_REGION=$(AWS_REGION)
	aws s3 sync cloudformation/ $(S3_DEV_BUCKET_URI) --acl public-read --exclude="*" --include="*.yml"

.PHONY: publish-prod-templates
publish-prod-templates:
	@export AWS_REGION=$(AWS_REGION)
	aws s3 sync cloudformation/ $(S3_PROD_BUCKET_URI) --exclude="*" --include="*.yml"

.PHONY: publish-versioned-templates
publish-versioned-templates:
	@export AWS_REGION=$(AWS_REGION)
	ci/publish_versioned_templates $(BRANCH) $(S3_PROD_BUCKET_URI) $(S3_PROD_STACK_URI) $(AMI_MAP_TEMP_FILE)

.PHONY: diff-dev-templates
diff-dev-templates:
	tempdir=`mktemp --directory`; aws s3 sync $(S3_DEV_BUCKET_URI) "$$tempdir" --exclude="*" --include="*.yml"; diff --recursive --unified "$$tempdir" cloudformation; rm -rf "$$tempdir"

.PHONY: diff-prod-templates
diff-prod-templates:
	tempdir=`mktemp --directory`; aws s3 sync $(S3_PROD_BUCKET_URI) "$$tempdir" --exclude="*" --include="*.yml"; diff --recursive --unified "$$tempdir" cloudformation; rm -rf "$$tempdir"

.PHONY: bind-domain-name
bind-domain-name:
	ci/bind_domain_name "$(DOMAIN_NAME)" "$(STACK_NAME)"
