FROM centos:7

MAINTAINER mozdef@mozilla.com

ENV KIBANA_VERSION 4.6.5

RUN curl -s -L https://download.elastic.co/kibana/kibana/kibana-$KIBANA_VERSION-linux-x86_64.tar.gz | tar -C / -xz

WORKDIR /kibana-$KIBANA_VERSION-linux-x86_64

EXPOSE 5601
