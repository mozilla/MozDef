FROM centos:7

MAINTAINER mozdef@mozilla.com

ENV KIBANA_VERSION 4.5.4

RUN curl -s -L https://download.elastic.co/kibana/kibana/kibana-$KIBANA_VERSION-linux-x64.tar.gz | tar -C / -xz

WORKDIR /kibana-$KIBANA_VERSION-linux-x64

EXPOSE 5601
