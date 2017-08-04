FROM centos:7

MAINTAINER mozdef@mozilla.com

ENV RABBITMQ_VERSION 3.3.5

RUN \
  yum makecache && \
  yum install -y epel-release && \
  rpm --import https://www.rabbitmq.com/rabbitmq-release-signing-key.asc && \
  yum install -y rabbitmq-server-$RABBITMQ_VERSION && \
  yum clean all

COPY files/rabbitmq.config /etc/rabbitmq/
COPY files/enabled_plugins /etc/rabbitmq/

EXPOSE 5672 15672
