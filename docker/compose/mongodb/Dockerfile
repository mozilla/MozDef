FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV MONGO_VERSION 3.2

RUN \
  echo -e "[mongodb-org-$MONGO_VERSION]\nname=MongoDB Repository\nbaseurl=https://repo.mongodb.org/yum/redhat/\$releasever/mongodb-org/$MONGO_VERSION/x86_64/\ngpgcheck=1\nenabled=1\ngpgkey=https://www.mongodb.org/static/pgp/server-$MONGO_VERSION.asc" > /etc/yum.repos.d/mongodb.repo && \
  yum install -y mongodb-org && \
  yum clean all

COPY files/mongod.conf /etc/mongod.conf

VOLUME /var/lib/mongo

EXPOSE 3002
