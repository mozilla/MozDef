FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV RABBITMQ_VERSION 3.3.5

RUN \
  yum makecache fast && \
  yum install -y epel-release && \
  rpm --import https://www.rabbitmq.com/rabbitmq-release-signing-key.asc && \
  yum install -y rabbitmq-server-$RABBITMQ_VERSION && \
  yum clean all

COPY docker/conf/rabbitmq.config /etc/rabbitmq/
COPY docker/conf/enabled_plugins /etc/rabbitmq/

EXPOSE 5672 15672
