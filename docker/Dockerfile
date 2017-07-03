# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Yohann Lepage yohann@lepage.info
# Anthony Verez averez@mozilla.com
# Charlie Lewis clewis@iqt.org

FROM debian:stable

MAINTAINER Jeff Bryner <jbryner@mozilla.com>

ENV DEBIAN_FRONTEND noninteractive
ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8

# Locales
RUN (apt-get clean \
        && apt-get -q -y update --fix-missing \
        && apt-get -q -y update \
        && apt-get install -q -y gnupg \
        && apt-get install -q -y apt-utils \
        && apt-get install -q -y locales \
        && apt-key update)

RUN echo "en_US.UTF-8 UTF-8\nen_US ISO-8859-1" > /etc/locale.gen
RUN (locale-gen \
        && locale-gen en_US.UTF-8 \
        && dpkg-reconfigure locales)

# install dependencies
RUN (apt-get install -q -y curl \
        git \
        libmysqlclient-dev \
        mongodb \
        nginx-full \
        nodejs \
        npm \
        openjdk-7-jre \
        python2.7-dev \
        python-pip \
        rabbitmq-server \
        supervisor \
        wget \
        && apt-get clean \
        && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/* /tmp/* /var/tmp/* \
        && rm /etc/nginx/nginx.conf)

# rabbit mq
RUN rabbitmq-plugins enable rabbitmq_management

RUN (pip install -U pip \
        && curl -L https://github.com/mozilla/MozDef/archive/master.tar.gz |tar -C /opt -xz \
        && /bin/ln -s /opt/MozDef-master /opt/MozDef \
        && cd /opt/MozDef && /usr/bin/pip install --verbose --use-mirrors --timeout 30 -r requirements.txt \
        && /usr/bin/pip install --verbose --use-mirrors --timeout 30 uwsgi celery \
        && mkdir /var/log/mozdef \
        && mkdir -p /run/uwsgi/apps/ \
        && touch /run/uwsgi/apps/loginput.socket && chmod 666 /run/uwsgi/apps/loginput.socket \
        && touch /run/uwsgi/apps/rest.socket && chmod 666 /run/uwsgi/apps/rest.socket \
        && mkdir -p /home/mozdef/envs/mozdef/bot/ && cd /home/mozdef/envs/mozdef/bot/ \
        && wget http://geolite.maxmind.com/download/geoip/database/GeoLiteCity.dat.gz && gzip -d GeoLiteCity.dat.gz)

# elasticsearch
RUN (curl -L https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.3.2.tar.gz  | tar -C /opt -xz \
        && /bin/ln -s /opt/elasticsearch-1.3.2 /opt/elasticsearch \
        && rm /opt/elasticsearch/config/elasticsearch.yml)
# Kibana
RUN (curl -L https://download.elasticsearch.org/kibana/kibana/kibana-3.1.0.tar.gz |tar -C /opt -xz \
        && /bin/ln -s /opt/kibana-3.1.0 /opt/kibana)
# Meteor
RUN (curl -L https://install.meteor.com/ | /bin/sh \
        && npm install -g meteorite \
        && ln -s /usr/bin/nodejs /usr/bin/node)
#can't add from the local relative dir, so add from github
ADD https://raw.githubusercontent.com/mozilla/MozDef/master/examples/kibana/dashboards/alert.js /opt/kibana/app/dashboards/alert.js
ADD https://raw.githubusercontent.com/mozilla/MozDef/master/examples/kibana/dashboards/event.js /opt/kibana/app/dashboards/event.js

# add configurations
COPY conf/supervisor.conf /etc/supervisor/conf.d/supervisor.conf
COPY conf/settings.js /opt/MozDef/meteor/app/lib/settings.js
COPY conf/config.py /opt/MozDef/alerts/lib/config.py
COPY conf/sampleData2MozDef.conf /opt/MozDef/examples/demo/sampleData2MozDef.conf
COPY conf/mozdef.localloginenabled.css /opt/MozDef/meteor/public/css/mozdef.css
COPY conf/syncalerts.sh /opt/MozDef/examples/demo/syncalerts.sh
COPY conf/nginx.conf /etc/nginx/
# COPY conf/elasticsearch/elasticsearch.yml /opt/elasticsearch/config/ # BUG https://github.com/dotcloud/docker/issues/2446
COPY conf/elasticsearch.yml /opt/elasticsearch-1.3.2/config/

# VOLUMES
#        Elasticsearch
VOLUME ['/var/lib/elasticsearch','/var/log/elasticsearch']
#        Mongodb
VOLUME ['/var/lib/mongodb','/var/log/mongodb']
#        Nginx
VOLUME ['/var/log/nginx','/var/log/mozdef']
#        Quick share resource
VOLUME ['/tmp/share','/tmp/share']

# PORTS
# METEOR, Elasticsearch, Kibana, LOGINPUT, REST
EXPOSE 3000 9200 9090 8080 8081

CMD /etc/init.d/supervisor start
