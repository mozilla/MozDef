FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV ES_VERSION 5.6.7
ENV ES_JAVA_VERSION 1.8.0

RUN \
  yum install -y java-$ES_JAVA_VERSION && \
  mkdir -p /opt/mozdef/envs && \
  curl -s -L https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-$ES_VERSION.tar.gz  | tar -C /opt/mozdef -xz && \
  mv /opt/mozdef/elasticsearch-$ES_VERSION /opt/mozdef/envs/elasticsearch && \
  yum clean all

COPY docker/conf/elasticsearch.yml /opt/mozdef/envs/elasticsearch/config/

WORKDIR /opt/mozdef/envs/elasticsearch

VOLUME /var/lib/elasticsearch

EXPOSE 9200
