FROM centos:7

MAINTAINER mozdef@mozilla.com

#updated meteor version to avoid EXDEV: cross-device link not permitted errors
ENV NODE_VERSION 4.7.0
ENV METEOR_VERSION 1.4.4.2
ENV METEOR_FILE_VERSION 1.4.4-1

ENV MONGO_URL=mongodb://mongodb:3002/meteor
ENV ROOT_URL=http://localhost
ENV PORT=3000

RUN \
  useradd -ms /bin/bash -d /opt/mozdef -m mozdef && \
  mkdir -p /opt/mozdef/envs/mozdef && \
  cd /opt/mozdef && \
  curl -sL -o /opt/mozdef/nodesource.rpm https://rpm.nodesource.com/pub_4.x/el/7/x86_64/nodesource-release-el7-1.noarch.rpm && \
  rpm -i --nosignature --force /opt/mozdef/nodesource.rpm && \
  yum install -y \
                    wget \
                    make \
                    glibc-devel \
                    gcc \
                    gcc-c++ \
                    libstdc++ \
                    libffi-devel \
                    zlib-devel && \
  yum install -y nodejs-$NODE_VERSION && \
  npm install source-map-support@0.4.2 \
                 semver@5.3.0 \
                 fibers@1.0.13 \
                 amdefine@1.0.0 \
                 underscore@1.8.3 \
                 bcrypt && \
  mkdir /opt/mozdef/meteor && \
  curl -sL -o /opt/mozdef/meteor.tar.gz https://static-meteor.netdna-ssl.com/packages-bootstrap/$METEOR_VERSION/meteor-bootstrap-os.linux.x86_64.tar.gz && \
  tar -xzf /opt/mozdef/meteor.tar.gz -C /opt/mozdef/meteor && \
  mv /opt/mozdef/meteor/.meteor /opt/mozdef && \
  rm -r /opt/mozdef/meteor && \
  cp /opt/mozdef/.meteor/packages/meteor-tool/*/mt-os.linux.x86_64/scripts/admin/launch-meteor /usr/bin/meteor

#copy our source dir and set ownership
USER mozdef
COPY meteor /opt/mozdef/envs/mozdef/meteor
USER root
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/meteor

#avoiding -R due to massive list of files from meteor
RUN chown  mozdef:mozdef /opt/mozdef/envs
USER mozdef
RUN \
  cd /opt/mozdef/envs/mozdef/meteor && \
  meteor npm install --save babel-runtime && \
  meteor add accounts-password && \
  meteor add npm-bcrypt && \
  mkdir -p /opt/mozdef/envs/meteor/mozdef

USER root
COPY docker/compose/mozdef_meteor/files/settings.js /opt/mozdef/envs/mozdef/meteor/app/lib/settings.js
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/meteor/app/lib/settings.js

USER mozdef
RUN \
  cd /opt/mozdef/envs/mozdef/meteor && \
  meteor build --server localhost:3002 --directory /opt/mozdef/envs/meteor/mozdef/ --allow-incompatible-update

WORKDIR /opt/mozdef/envs/meteor/mozdef

EXPOSE 3000
