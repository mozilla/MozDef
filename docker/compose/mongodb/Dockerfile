FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV MONGO_VERSION 3.4

RUN \
  echo -e "[mongodb-org-$MONGO_VERSION]\n\
name=MongoDB Repository\n\
baseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/$MONGO_VERSION/x86_64/\n\
gpgcheck=1\n\
enabled=1\n\
gpgkey=https://www.mongodb.org/static/pgp/server-$MONGO_VERSION.asc" > /etc/yum.repos.d/mongodb.repo && \
  gpg="gpg --no-default-keyring --secret-keyring /dev/null --keyring /dev/null --no-option --keyid-format 0xlong" && \
  rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 && \
  rpm -qi gpg-pubkey-f4a80eb5 | $gpg | grep 0x24C6A8A7F4A80EB5 && \
  rpmkeys --import https://www.mongodb.org/static/pgp/server-3.4.asc && \
  rpm -qi gpg-pubkey-a15703c6 | $gpg | grep 0xBC711F9BA15703C6 && \
  yum install -y mongodb-org && \
  yum clean all && \
  rm -rf /var/cache/yum

COPY docker/compose/mongodb/files/mongod.conf /etc/mongod.conf

VOLUME /var/lib/mongo

EXPOSE 3002
