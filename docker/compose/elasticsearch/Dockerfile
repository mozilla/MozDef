FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV ES_VERSION 6.6.2
ENV ES_JAVA_VERSION 1.8.0


RUN \
  yum install -y java-$ES_JAVA_VERSION && \
  mkdir -p /opt/mozdef/envs && \
  curl -s -L https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-$ES_VERSION.rpm -o elasticsearch.rpm && \
  rpm -i elasticsearch.rpm && \
  yum clean all

USER elasticsearch

COPY docker/compose/elasticsearch/files/elasticsearch.yml /etc/elasticsearch/elasticsearch.yml
COPY docker/compose/elasticsearch/files/jvm.options /etc/elasticsearch/jvm.options

VOLUME /var/lib/elasticsearch

WORKDIR /usr/share/elasticsearch

EXPOSE 9200
