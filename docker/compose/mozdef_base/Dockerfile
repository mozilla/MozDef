FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV TZ UTC

RUN \
  yum makecache fast && \
  yum install -y epel-release && \
  yum install -y \
                  glibc-devel \
                  gcc \
                  libstdc++ \
                  libffi-devel \
                  zlib-devel \
                  git \
                  make && \
  useradd -ms /bin/bash -d /opt/mozdef -m mozdef && \
  mkdir /opt/mozdef/envs && \
  cd /opt/mozdef && \
  yum install -y mysql-devel \
                    python \
                    python-devel \
                    python-pip && \
  pip install virtualenv && \
  mkdir /opt/mozdef/envs/mozdef && \
  mkdir /opt/mozdef/envs/mozdef/cron

# Create python virtual environment and install dependencies
COPY requirements.txt /opt/mozdef/envs/mozdef/requirements.txt

COPY cron/update_geolite_db.py /opt/mozdef/envs/mozdef/cron/update_geolite_db.py
COPY cron/update_geolite_db.conf /opt/mozdef/envs/mozdef/cron/update_geolite_db.conf
COPY cron/update_geolite_db.sh /opt/mozdef/envs/mozdef/cron/update_geolite_db.sh

RUN chown -R mozdef:mozdef /opt/mozdef/
USER mozdef
RUN \
  virtualenv /opt/mozdef/envs/python && \
  source /opt/mozdef/envs/python/bin/activate && \
  pip install -r /opt/mozdef/envs/mozdef/requirements.txt

# Local copy for dev
COPY mozdef_util /opt/mozdef/envs/mozdef/mozdef_util
USER root
RUN \
  source /opt/mozdef/envs/python/bin/activate && \
  cd /opt/mozdef/envs/mozdef/mozdef_util && \
  pip install -e .
RUN chown -R mozdef:mozdef /opt/mozdef/

USER mozdef

RUN mkdir /opt/mozdef/envs/mozdef/data

WORKDIR /opt/mozdef/envs/mozdef

VOLUME /opt/mozdef/envs/mozdef/data

USER root
