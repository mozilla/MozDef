FROM centos:7

MAINTAINER mozdef@mozilla.com

RUN \
  mkdir /var/log/mozdef && \
  yum install -y epel-release && \
  yum install -y nginx


COPY files/nginx.conf /etc/nginx/nginx.conf

EXPOSE 80 9090
