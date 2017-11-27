FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV KIBANA_VERSION 4.6.5

RUN curl -s -L https://download.elastic.co/kibana/kibana/kibana-$KIBANA_VERSION-linux-x86_64.tar.gz | tar -C / -xz && \
    cd /kibana-$KIBANA_VERSION-linux-x86_64 && \
    bin/kibana plugin --install elastic/sense

WORKDIR /kibana-$KIBANA_VERSION-linux-x86_64

EXPOSE 5601
