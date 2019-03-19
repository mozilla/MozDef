FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV RABBITMQ_VERSION 3.7.13

COPY docker/compose/rabbitmq/files/rabbitmq-server.repo /etc/yum.repos.d/rabbitmq-server.repo
COPY docker/compose/rabbitmq/files/erlang.repo /etc/yum.repos.d/erlang.repo

RUN \
  yum -q makecache -y fast && \
  yum install -y epel-release && \
  yum install -y rabbitmq-server-$RABBITMQ_VERSION && \
  yum clean all

COPY docker/compose/rabbitmq/files/rabbitmq.config /etc/rabbitmq/
COPY docker/compose/rabbitmq/files/enabled_plugins /etc/rabbitmq/

EXPOSE 5672 15672
