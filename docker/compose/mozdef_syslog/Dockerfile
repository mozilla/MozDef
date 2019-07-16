FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

COPY docker/compose/mozdef_syslog/files/syslog-ng.repo /etc/yum.repos.d/syslog-ng.repo

RUN \
  gpg="gpg --no-default-keyring --secret-keyring /dev/null --keyring /dev/null --no-option --keyid-format 0xlong" && \
  rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 && \
  rpm -qi gpg-pubkey-f4a80eb5 | $gpg | grep 0x24C6A8A7F4A80EB5 && \
  rpmkeys --import https://copr-be.cloud.fedoraproject.org/results/czanik/syslog-ng312/pubkey.gpg && \
  rpm -qi gpg-pubkey-2b04b9af | $gpg | grep 0x1AACFE032B04B9AF && \
  rpmkeys --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-7 && \
  rpm -qi gpg-pubkey-352c64e5 | $gpg | grep 0x6A2FAEA2352C64E5 && \
  yum install -y epel-release && \
  yum install -y syslog-ng.x86_64 syslog-ng-json && \
  yum clean all && \
  rm -rf /var/cache/yum

COPY docker/compose/mozdef_syslog/files/syslog-ng.conf /etc/syslog-ng/syslog-ng.conf

EXPOSE 514/udp
EXPOSE 514
