FROM centos:7

MAINTAINER mozdef@mozilla.com

ENV ES_VERSION 2.4.2
ENV ES_JAVA_VERSION 1.8.0

RUN \
  yum install -y java-$ES_JAVA_VERSION && \
  curl -s -L https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-$ES_VERSION.tar.gz  | tar -C / -xz && \
  yum clean all

WORKDIR /elasticsearch-$ES_VERSION

VOLUME /usr/share/elasticsearch/data

EXPOSE 9200
