FROM mozdef_base:latest

MAINTAINER mozdef@mozilla.com

ENV NODE_VERSION 4.7.0
ENV METEOR_VERSION 1.4.0.1
ENV METEOR_FILE_VERSION 1.4.0-1

ENV MONGO_URL=mongodb://mongodb:3002/meteor
ENV ROOT_URL=http://localhost
ENV PORT=3000

RUN \
  cd /opt/mozdef && \
  curl -sL -o /opt/mozdef/nodesource.rpm https://rpm.nodesource.com/pub_4.x/el/7/x86_64/nodesource-release-el7-1.noarch.rpm && \
  rpm -i --nosignature --force /opt/mozdef/nodesource.rpm && \
  yum install -y nodejs-$NODE_VERSION && \
  npm install source-map-support@0.4.2 \
                 semver@5.3.0 \
                 fibers@1.0.13 \
                 amdefine@1.0.0 \
                 underscore@1.8.3 \
                 bcrypt && \
  mkdir /opt/mozdef/meteor && \
  curl -sL -o /opt/mozdef/meteor.tar.gz https://meteorinstall-4168.kxcdn.com/packages-bootstrap/$METEOR_VERSION/meteor-bootstrap-os.linux.x86_64.tar.gz && \
  tar -xzf /opt/mozdef/meteor.tar.gz -C /opt/mozdef/meteor && \
  mv /opt/mozdef/meteor/.meteor /opt/mozdef && \
  rm -r /opt/mozdef/meteor && \
  cp /opt/mozdef/.meteor/packages/meteor-tool/$METEOR_FILE_VERSION/mt-os.linux.x86_64/scripts/admin/launch-meteor /usr/bin/meteor

COPY meteor /opt/mozdef/envs/mozdef/meteor
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/meteor
RUN chown -R mozdef:mozdef /opt/mozdef/

USER mozdef
RUN \
  cd /opt/mozdef/envs/mozdef/meteor && \
  meteor npm install --save babel-runtime && \
  meteor add accounts-password && \
  meteor add npm-bcrypt && \
  mkdir -p /opt/mozdef/envs/meteor/mozdef && \
  meteor build --server localhost:3002 --directory /opt/mozdef/envs/meteor/mozdef/ --allow-incompatible-update

WORKDIR /opt/mozdef/envs/meteor/mozdef

EXPOSE 3000
