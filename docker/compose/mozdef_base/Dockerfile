FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV PYTHON_VERSION 2.7.11
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
                  make && \
  useradd -ms /bin/bash -d /opt/mozdef -m mozdef && \
  mkdir /opt/mozdef/envs && \
  curl -s -L https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz  | tar -C /opt/mozdef/ -xz && \
  cd /opt/mozdef/Python-$PYTHON_VERSION && \
  ./configure && \
  make && \
  make install && \
  rm -r /opt/mozdef/Python-$PYTHON_VERSION && \
  cd /opt/mozdef && \
  yum install -y mysql-devel \
                    python-devel \
                    python-pip && \
  chown -R mozdef:mozdef /opt/mozdef/ && \
  pip install virtualenv && \
  mkdir /opt/mozdef/envs/mozdef && \
  mkdir /opt/mozdef/envs/mozdef/cron

# Create python virtual environment and install dependencies
COPY requirements.txt /opt/mozdef/envs/mozdef/requirements.txt

COPY cron/update_geolite_db.py /opt/mozdef/envs/mozdef/cron/update_geolite_db.py
COPY cron/update_geolite_db.conf /opt/mozdef/envs/mozdef/cron/update_geolite_db.conf
COPY cron/update_geolite_db.sh /opt/mozdef/envs/mozdef/cron/update_geolite_db.sh

USER mozdef
RUN \
  virtualenv /opt/mozdef/envs/python && \
  source /opt/mozdef/envs/python/bin/activate && \
  pip install -r /opt/mozdef/envs/mozdef/requirements.txt

COPY lib /opt/mozdef/envs/mozdef/lib

USER root
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef

USER mozdef
# We have to replace the python virtualenv path until
# https://github.com/mozilla/MozDef/issues/421 is fixed
RUN sed -i 's|/opt/mozdef/envs/mozdef/bin/activate|/opt/mozdef/envs/python/bin/activate|g' /opt/mozdef/envs/mozdef/cron/*.sh

RUN mkdir /opt/mozdef/envs/mozdef/data

WORKDIR /opt/mozdef/envs/mozdef

VOLUME /opt/mozdef/envs/mozdef/data

USER root
