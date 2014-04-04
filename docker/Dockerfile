FROM debian:testing

MAINTAINER Yohann Lepage <yohann@lepage.info>

ENV DEBIAN_FRONTEND noninteractive

# Locales
RUN (apt-key update \
	&& apt-get -q -y update \
	&& apt-get install -q -y apt-utils \
	&& apt-get install -q -y locales)

ADD conf/locale.gen /etc/locale.gen
RUN (locale-gen \
	&& locale-gen en_US.UTF-8 \
	&& dpkg-reconfigure locales)

ENV LANGUAGE en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
ENV LC_CTYPE en_US.UTF-8

RUN apt-get install -q -y openjdk-7-jre

# rabbit mq
RUN apt-get install -q -y rabbitmq-server
# mongodb
RUN apt-get install -q -y mongodb
# nodejs
RUN apt-get install -q -y nodejs npm git
# nginx
RUN (apt-get install -q -y nginx-full \
	&& rm /etc/nginx/nginx.conf)
ADD conf/nginx.conf /etc/nginx/


#Mozdef
RUN (apt-get install -q -y python2.7-dev python-pip curl supervisor\
        && curl -L https://github.com/jeffbryner/MozDef/archive/master.tar.gz |tar -C /opt -xz \
        && /bin/ln -s /opt/MozDef-master /opt/MozDef \
	&& cd /opt/MozDef && /usr/bin/pip install --verbose --use-mirrors --timeout 30 -r requirements.txt \
	&& /usr/bin/pip install --verbose --use-mirrors --timeout 30 uwsgi gevent \
	&& mkdir /var/log/mozdef \
	&& mkdir -p /run/uwsgi/apps/ \
	&& touch /run/uwsgi/apps/loginput.socket && chmod 666 /run/uwsgi/apps/loginput.socket \
	&& touch /run/uwsgi/apps/rest.socket && chmod 666 /run/uwsgi/apps/rest.socket)
ADD conf/supervisor.conf /etc/supervisor/conf.d/supervisor.conf


# elasticsearch
RUN (curl -L https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.0.1.tar.gz  | tar -C /opt -xz \
	&& /bin/ln -s /opt/elasticsearch-1.0.1 /opt/elasticsearch \
	&& /opt/elasticsearch/bin/plugin --install elasticsearch/marvel/latest \
	&& rm /opt/elasticsearch/config/elasticsearch.yml)
# ADD conf/elasticsearch/elasticsearch.yml /opt/elasticsearch/config/ # BUG https://github.com/dotcloud/docker/issues/2446
ADD conf/elasticsearch.yml /opt/elasticsearch-1.0.1/config/


# Kibana
RUN (curl -L https://download.elasticsearch.org/kibana/kibana/kibana-3.0.0.tar.gz |tar -C /opt -xz \
	&& /bin/ln -s /opt/kibana-3.0.0 /opt/kibana \
	&& cp /opt/MozDef/kibana/dashboards/* /opt/kibana/app/dashboards/ \
	&& sed -i 's#/dashboard/file/default.json#/dashboard/file/mozdefAlerts.json#g' /opt/kibana/config.js)


# Meteor
RUN (curl -L https://install.meteor.com/ | /bin/sh \
	&& npm install -g meteorite \
	&& ln -s /usr/bin/nodejs /usr/bin/node \
	&& cd /opt/MozDef/meteor \
	&& mrt update \
	&& /usr/local/bin/mrt add iron-router \
	&& /usr/local/bin/mrt add accounts-persona)


# VOLUMES
#	Elasticsearch
VOLUME ['/var/lib/elasticsearch','/var/log/elasticsearch']
#	Mongodb
VOLUME ['/var/lib/mongodb','/var/log/mongodb']
#	Nginx
VOLUME ['/var/log/nginx','/var/log/mozdef']

# PORTS
#       METEOR
EXPOSE 3000
#       Elasticsearch
EXPOSE 9200
# 	Kibana
EXPOSE 9090
# 	LOGINPUT
EXPOSE 8080
#	REST
EXPOSE 8081

# CLEAN
RUN apt-get clean && rm -rf /var/cache/apt/archives/* /var/lib/apt/lists/*

CMD ["/usr/bin/supervisord"]
