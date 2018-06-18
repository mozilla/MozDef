FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

COPY docker/compose/mozdef_syslog/files/syslog-ng.repo /etc/yum.repos.d/syslog-ng.repo

RUN \
  yum install -y epel-release && \
  yum install -y syslog-ng.x86_64 syslog-ng-json && \
  yum clean all

COPY docker/compose/mozdef_syslog/files/syslog-ng.conf /etc/syslog-ng/syslog-ng.conf

EXPOSE 514/udp
EXPOSE 514
