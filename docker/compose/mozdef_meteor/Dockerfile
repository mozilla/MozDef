FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV NODE_VERSION 8.11.4
ENV METEOR_VERSION 1.8

ENV MONGO_URL=mongodb://mongodb:3002/meteor
ENV ROOT_URL=http://localhost
ENV PORT=3000

ARG METEOR_BUILD='YES'

# Ignore warnings like 'No such file or directory for /usr/share/info/*.info.gz"
# https://bugzilla.redhat.com/show_bug.cgi?id=516757

RUN \
  useradd --create-home --shell /bin/bash --home-dir /opt/mozdef mozdef && \
  cd /opt/mozdef && \
  gpg="gpg --no-default-keyring --secret-keyring /dev/null --keyring /dev/null --no-option --keyid-format 0xlong" && \
  rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 && \
  rpm -qi gpg-pubkey-f4a80eb5 | $gpg | grep 0x24C6A8A7F4A80EB5 && \
  yum makecache fast && \
  yum install -y which && \
  curl --silent --location https://rpm.nodesource.com/setup_8.x | bash - && \
  rpmkeys --import /etc/pki/rpm-gpg/NODESOURCE-GPG-SIGNING-KEY-EL && \
  rpm -qi gpg-pubkey-34fa74dd | $gpg | grep 0x5DDBE8D434FA74DD && \
  yum install -y \
     make \
     glibc-devel \
     gcc \
     gcc-c++ \
     libstdc++ \
     zlib-devel \
     nodejs && \
  yum clean all && \
  rm -rf /var/cache/yum && \
  echo "Downloading meteor" && \
  curl --silent --location https://static-meteor.netdna-ssl.com/packages-bootstrap/$METEOR_VERSION/meteor-bootstrap-os.linux.x86_64.tar.gz \
    | tar --extract --gzip --directory /opt/mozdef .meteor && \
  ln --symbolic /opt/mozdef/.meteor/packages/meteor-tool/*/mt-os.linux.x86_64/scripts/admin/launch-meteor /usr/bin/meteor && \
  install --owner mozdef --group mozdef --directory /opt/mozdef/envs /opt/mozdef/envs/mozdef

COPY --chown=mozdef:mozdef meteor /opt/mozdef/envs/mozdef/meteor
COPY --chown=mozdef:mozdef docker/compose/mozdef_meteor/files/settings.js /opt/mozdef/envs/mozdef/meteor/imports/settings.js

USER mozdef

# build meteor runtime if asked, if set to NO, only create the dir created above to mount to do live development
RUN \
  mkdir -p /opt/mozdef/envs/meteor/mozdef && \
  cd /opt/mozdef/envs/mozdef/meteor && \
  meteor npm install && \
  if [ "${METEOR_BUILD}" = "YES" ]; then \
    echo "Starting meteor build" && \
    time meteor build --server localhost:3002 --directory /opt/mozdef/envs/meteor/mozdef && \
    ln --symbolic /opt/mozdef/envs/meteor/mozdef/node_modules /opt/mozdef/envs/mozdef/meteor/node_modules && \
    cd /opt/mozdef/envs/meteor/mozdef/bundle/programs/server && \
    npm install ;\
  fi

WORKDIR /opt/mozdef/envs/meteor/mozdef

EXPOSE 3000
