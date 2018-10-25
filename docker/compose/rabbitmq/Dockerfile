FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV RABBITMQ_VERSION 3.3.5

RUN \
  yum makecache fast && \
  yum install -y epel-release && \
  rpm --import https://www.rabbitmq.com/rabbitmq-release-signing-key.asc && \
  yum install -y rabbitmq-server-$RABBITMQ_VERSION && \
  yum clean all

COPY docker/compose/rabbitmq/files/rabbitmq.config /etc/rabbitmq/
COPY docker/compose/rabbitmq/files/enabled_plugins /etc/rabbitmq/

EXPOSE 5672 15672
