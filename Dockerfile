# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com
# Yohann Lepage yohann@lepage.info
# Anthony Verez averez@mozilla.com
# Charlie Lewis clewis@iqt.org
# Brandon Myers bmyers@mozilla.com

FROM centos:7

MAINTAINER mozdef@mozilla.com

ENV METEOR_VERSION 1.4.0.1
ENV PYTHON_VERSION 2.7.11
ENV KIBANA_VERSION 4.5.4
ENV ES_VERSION 2.4.2
ENV ES_JAVA_VERSION 1.8.0
ENV RABBITMQ_VERSION 3.3.5

ENV MONGO_URL=mongodb://localhost:3002/meteor
ENV ROOT_URL=http://localhost
ENV PORT=3000

COPY docker/conf/mongodb.repo /etc/yum.repos.d/mongodb.repo

RUN \
  yum clean all \
  && yum install -y epel-release \
  && yum install -y \
                    wget \
                    java-$ES_JAVA_VERSION \
                    glibc-devel \
                    gcc \
                    libstdc++ \
                    supervisor \
                    libffi-devel \
                    zlib-devel \
  && useradd -ms /bin/bash -d /opt/mozdef -m mozdef \
  && mkdir /opt/mozdef/envs \
  && curl -s -L https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-$ES_VERSION.tar.gz  | tar -C /opt/mozdef -xz \
  && mv /opt/mozdef/elasticsearch-$ES_VERSION /opt/mozdef/envs/elasticsearch \
  && rpm --import https://www.rabbitmq.com/rabbitmq-release-signing-key.asc \
  && yum install -y rabbitmq-server-$RABBITMQ_VERSION \
  && yum install -y nginx \
  && mkdir /var/log/mozdef/ \
  && curl -s -L https://download.elastic.co/kibana/kibana/kibana-$KIBANA_VERSION-linux-x64.tar.gz | tar -C /opt/mozdef/ -xz \
  && mv /opt/mozdef/kibana-$KIBANA_VERSION-linux-x64 /opt/mozdef/envs/kibana \
  && yum install -y mongodb-org \
  && curl -s -L https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz  | tar -C /opt/mozdef/ -xz \
  && cd /opt/mozdef/Python-$PYTHON_VERSION \
  && ./configure \
  && make \
  && make install \
  && rm -r /opt/mozdef/Python-$PYTHON_VERSION \
  && cd /opt/mozdef \
  && yum install -y mysql-devel \
                    python-devel \
                    python-pip \
  && chown -R mozdef:mozdef /opt/mozdef/ \
  && pip install virtualenv

# Node
USER root
COPY docker/conf/nodesource.sh /opt/mozdef/nodesource.sh
RUN \
  chmod u+x /opt/mozdef/nodesource.sh \
  && /opt/mozdef/nodesource.sh \
  && yum install -y nodejs-4.7.0 \
  && npm install source-map-support@0.4.2 \
                 semver@5.3.0 \
                 fibers@1.0.13 \
                 amdefine@1.0.0 \
                 underscore@1.8.3 \
                 bcrypt

## Meteor
USER root
COPY docker/conf/meteor.sh /opt/mozdef/meteor.sh
RUN chmod a+x /opt/mozdef/meteor.sh
USER mozdef
RUN /opt/mozdef/meteor.sh
USER root
RUN cp "/opt/mozdef/.meteor/packages/meteor-tool/1.4.0-1/mt-os.linux.x86_64/scripts/admin/launch-meteor" /usr/bin/meteor

COPY meteor /opt/mozdef/envs/mozdef/src/meteor
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/src/meteor
USER mozdef
RUN \
  cd /opt/mozdef/envs/mozdef/src/meteor \
  && meteor npm install --save babel-runtime \
  && meteor add accounts-password \
  && meteor add npm-bcrypt \
  && mkdir -p /opt/mozdef/envs/meteor/mozdef \
  && meteor build --server localhost:3002 --directory /opt/mozdef/envs/meteor/mozdef/ --allow-incompatible-update

COPY requirements.txt /opt/mozdef/envs/mozdef/src/requirements.txt
USER mozdef
RUN \
  virtualenv /opt/mozdef/envs/python \
  && source /opt/mozdef/envs/python/bin/activate \
  && pip install -r /opt/mozdef/envs/mozdef/src/requirements.txt

COPY docker/conf/elasticsearch.yml /opt/mozdef/envs/elasticsearch/config/
COPY docker/conf/supervisor.conf /etc/supervisor/conf.d/supervisor.conf
COPY docker/conf/mongod.conf /etc/mongod.conf
COPY docker/conf/rabbitmq.config /etc/rabbitmq/
COPY docker/conf/enabled_plugins /etc/rabbitmq/
COPY docker/conf/nginx.conf /etc/nginx/nginx.conf

COPY static /opt/mozdef/envs/mozdef/src/static
COPY rest /opt/mozdef/envs/mozdef/src/rest
COPY loginput /opt/mozdef/envs/mozdef/src/loginput
COPY bot /opt/mozdef/envs/mozdef/src/bot
COPY lib /opt/mozdef/envs/mozdef/src/lib
COPY cron /opt/mozdef/envs/mozdef/src/cron
COPY alerts /opt/mozdef/envs/mozdef/src/alerts
COPY mq /opt/mozdef/envs/mozdef/src/mq

USER root
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/src

# 80 = MozDef Web UI (meteor)
# 9200 = Elasticsearch
# 5672 = RabbitMQ endpoint
# 15672 = RabbitMQ Management endpoint (private by default)
# 5601 = Kibana Web UI
# 3002 = Mongodb (private by default)
# 8080 = Loginput
# 8081 = RestAPI
EXPOSE 80 9200 5672 5601 8080 8081

CMD supervisord -n -c /etc/supervisor/conf.d/supervisor.conf