FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV RABBITMQ_VERSION 3.7.13

COPY docker/compose/rabbitmq/files/rabbitmq-server.repo /etc/yum.repos.d/rabbitmq-server.repo
COPY docker/compose/rabbitmq/files/erlang.repo /etc/yum.repos.d/erlang.repo

RUN \
  gpg="gpg --no-default-keyring --secret-keyring /dev/null --keyring /dev/null --no-option --keyid-format 0xlong" && \
  rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 && \
  rpm -qi gpg-pubkey-f4a80eb5 | $gpg | grep 0x24C6A8A7F4A80EB5 && \
  yum --quiet makecache -y fast && \
  yum install -y rabbitmq-server-$RABBITMQ_VERSION && \
  yum clean all && \
  rm -rf /var/cache/yum

COPY docker/compose/rabbitmq/files/rabbitmq.config /etc/rabbitmq/
COPY docker/compose/rabbitmq/files/enabled_plugins /etc/rabbitmq/

EXPOSE 5672 15672
