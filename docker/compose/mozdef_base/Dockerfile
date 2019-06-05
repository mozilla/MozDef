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
                  libcurl-devel \
                  openssl \
                  openssl-devel \
                  git \
                  make && \
  useradd -ms /bin/bash -d /opt/mozdef -m mozdef && \
  mkdir /opt/mozdef/envs && \
  cd /opt/mozdef && \
  yum install -y python \
                    python-devel \
                    python-pip && \
  yum clean all && \
  pip install virtualenv && \
  mkdir /opt/mozdef/envs/mozdef && \
  mkdir /opt/mozdef/envs/mozdef/cron

# Force pycurl to understand we prefer nss backend
# Pycurl with ssl support is required by kombu in order to use SQS
ENV PYCURL_SSL_LIBRARY=nss

# Create python virtual environment and install dependencies
COPY requirements.txt /opt/mozdef/envs/mozdef/requirements.txt

COPY cron/update_geolite_db.py /opt/mozdef/envs/mozdef/cron/update_geolite_db.py
COPY cron/update_geolite_db.conf /opt/mozdef/envs/mozdef/cron/update_geolite_db.conf
COPY cron/update_geolite_db.sh /opt/mozdef/envs/mozdef/cron/update_geolite_db.sh

COPY mozdef_util /opt/mozdef/envs/mozdef/mozdef_util

RUN chown -R mozdef:mozdef /opt/mozdef/

USER mozdef
RUN \
  virtualenv /opt/mozdef/envs/python && \
  source /opt/mozdef/envs/python/bin/activate && \
  pip install -r /opt/mozdef/envs/mozdef/requirements.txt && \
  cd /opt/mozdef/envs/mozdef/mozdef_util && \
  pip install -e .

RUN mkdir /opt/mozdef/envs/mozdef/data

WORKDIR /opt/mozdef/envs/mozdef

VOLUME /opt/mozdef/envs/mozdef/data

# Automatically source into python virtual environment
ENV PATH=/opt/mozdef/envs/python/bin:$PATH

USER root
