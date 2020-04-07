FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV KIBANA_VERSION 6.8.0

RUN \
  mkdir /kibana && \
  curl --silent --location https://artifacts.elastic.co/downloads/kibana/kibana-$KIBANA_VERSION-linux-x86_64.tar.gz \
    | tar --extract --gzip --strip 1 --directory /kibana

COPY docker/compose/kibana/files/kibana.yml /kibana/config/kibana.yml

WORKDIR /kibana

EXPOSE 5601
