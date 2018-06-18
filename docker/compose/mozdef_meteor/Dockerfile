FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV NODE_VERSION 4.7.0
ENV METEOR_VERSION 1.4.2.3

ENV MONGO_URL=mongodb://mongodb:3002/meteor
ENV ROOT_URL=http://localhost
ENV PORT=3000

RUN \
  useradd -ms /bin/bash -d /opt/mozdef -m mozdef && \
  mkdir -p /opt/mozdef/envs/mozdef && \
  cd /opt/mozdef && \
  chown -R mozdef:mozdef /opt/mozdef && \
  yum install -y \
                wget \
                make \
                glibc-devel \
                gcc \
                gcc-c++ \
                libstdc++ \
                libffi-devel \
                zlib-devel && \
  curl -sL -o /opt/mozdef/nodesource.rpm https://rpm.nodesource.com/pub_4.x/el/7/x86_64/nodesource-release-el7-1.noarch.rpm && \
  rpm -i --nosignature --force /opt/mozdef/nodesource.rpm && \
  yum install -y nodejs-$NODE_VERSION && \
  mkdir /opt/mozdef/meteor && \
  curl -sL -o /opt/mozdef/meteor.tar.gz https://static-meteor.netdna-ssl.com/packages-bootstrap/$METEOR_VERSION/meteor-bootstrap-os.linux.x86_64.tar.gz && \
  tar -xzf /opt/mozdef/meteor.tar.gz -C /opt/mozdef/meteor && \
  mv /opt/mozdef/meteor/.meteor /opt/mozdef && \
  rm -r /opt/mozdef/meteor && \
  cp /opt/mozdef/.meteor/packages/meteor-tool/*/mt-os.linux.x86_64/scripts/admin/launch-meteor /usr/bin/meteor

COPY meteor /opt/mozdef/envs/mozdef/meteor
COPY docker/compose/mozdef_meteor/files/settings.js /opt/mozdef/envs/mozdef/meteor/app/lib/settings.js
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/meteor

USER mozdef
RUN \
  mkdir -p /opt/mozdef/envs/meteor/mozdef && \
  cd /opt/mozdef/envs/mozdef/meteor && \
  meteor npm install && \
  meteor build --server localhost:3002 --directory /opt/mozdef/envs/meteor/mozdef && \
  mv /opt/mozdef/envs/mozdef/meteor/node_modules /opt/mozdef/envs/meteor/mozdef/node_modules

WORKDIR /opt/mozdef/envs/meteor/mozdef

EXPOSE 3000