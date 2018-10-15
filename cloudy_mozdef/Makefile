ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]].*:' Makefile

docker-build:
	docker build -t mozdef-deployment:latest .

deploy-shell:
	docker run -ti -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest /bin/bash

packer-build:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'cd packer && packer build packer.json'

deploy-nested-cloudformation:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'ansible-playbook -c local ansible/update-ami-metadata.yml'
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'aws s3 sync /opt/mozdef/ansible/files/stacks/ s3://mozdef.infosec.mozilla.org/cf/ --acl public-read'

test-nested-stack:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'ansible-playbook -c local ansible/update-ami-metadata.yml'
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'aws s3 sync /opt/mozdef/ansible/files/stacks/ s3://mozdef.infosec.mozilla.org/cf/ --acl public-read'
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'aws s3 cp /opt/mozdef/cloudformation/nested-stack.yml s3://mozdef.infosec.mozilla.org/cf/nested-stack.yml --acl public-read'
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'aws cloudformation update-stack --stack-name mozdef-nested --template-url https://s3-us-west-2.amazonaws.com/cf/nested-stack.yml'

stack-status:
	docker run -v ~/.aws:/root/.aws -v `pwd`:/opt/mozdef mozdef-deployment:latest bash -c 'aws cloudformation describe-stacks --stack-name mozdef-nested'
