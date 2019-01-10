FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

RUN \
  gpg="gpg --no-default-keyring --secret-keyring /dev/null --keyring /dev/null --no-option --keyid-format 0xlong" && \
  rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 && \
  rpm -qi gpg-pubkey-f4a80eb5 | $gpg | grep 0x24C6A8A7F4A80EB5 && \
  mkdir /var/log/mozdef && \
  yum makecache fast && \
  rpmkeys --import https://dl.fedoraproject.org/pub/epel/RPM-GPG-KEY-EPEL-7 && \
  rpm -qi gpg-pubkey-352c64e5 | $gpg | grep 0x6A2FAEA2352C64E5 && \
  yum install -y epel-release && \
  yum install -y nginx && \
  yum clean all


COPY docker/compose/nginx/files/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 9090
