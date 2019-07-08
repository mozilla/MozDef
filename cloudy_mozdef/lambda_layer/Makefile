# Makefile to build and pack a lambda layer containing MozDef Alert Capabilities

ROOT_DIR	:= $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
STAGE			:= ${STAGE}
STAGE			:= $(if $(STAGE),$(STAGE),testing)
PYDIR			:= python/
all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]^\.PHONY.*].*:' Makefile

.PHONY: clean
clean:
	rm -rf $(ROOT_DIR)/build/*

.PHONY: deploy-shell
deploy-shell:
	docker run -ti -v ~/.aws:/root/.aws -v ${PWD}:/var/task mozdef/mozdef_base:latest

.PHONY: package-layer
package-layer: clean
	rm -rf $(ROOT_DIR)/layer-latest.zip
	docker run -ti -v ~/.aws:/root/.aws -v ${PWD}:/var/task mozdef/mozdef_base:latest pip install -r requirements.txt -t /var/task/cloudy_mozdef/lambda_layer/build/${PYDIR}
	docker run -ti -v ~/.aws:/root/.aws -v ${PWD}:/var/task mozdef/mozdef_base:latest pip install /var/task/mozdef_util/ -t /var/task/cloudy_mozdef/lambda_layer/build/${PYDIR}
	docker run -ti -v ~/.aws:/root/.aws -v ${PWD}:/var/task mozdef/mozdef_base:latest bash -c "yum install zip -y && cd /var/task/cloudy_mozdef/lambda_layer/build/ && \
	zip -r /var/task/cloudy_mozdef/lambda_layer/layer-latest.zip . "

.PHONY: package-function
package-function: clean
	rm -rf $(ROOT_DIR)/function-latest.zip
	cp ${PWD}/cloudy_mozdef/lambda_layer/lambdalert.py ${PWD}/cloudy_mozdef/lambda_layer/build/
	cp -r ${PWD}/alerts/lib ${PWD}/cloudy_mozdef/lambda_layer/build/
	docker run -ti -v ~/.aws:/root/.aws -v ${PWD}:/var/task mozdef/mozdef_base:latest \
	bash -c "yum install zip -y && cd /var/task/cloudy_mozdef/lambda_layer/build && \
		zip -r /var/task/cloudy_mozdef/lambda_layer/function-latest.zip ."

.PHONY: upload-s3
upload-s3:
	aws s3 cp ${PWD}/cloudy_mozdef/lambda_layer/layer-latest.zip s3://public.us-west-2.security.allizom.org/mozdef-lambda-layer/layer-latest.zip
	aws s3 cp ${PWD}/cloudy_mozdef/lambda_layer/function-latest.zip s3://public.us-west-2.security.allizom.org/mozdef-lambda-layer/function-latest.zip

.PHONY: publish-layer
publish-layer: upload-s3
	aws lambda publish-layer-version \
		--layer-name mozdef --compatible-runtimes python3.6 \
		--content S3Bucket=public.us-west-2.security.allizom.org,S3Key=mozdef-lambda-layer/layer-latest.zip

