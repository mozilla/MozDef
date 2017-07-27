FROM centos:7

MAINTAINER mozdef@mozilla.com

ENV PYTHON_VERSION 2.7.11
ENV TZ UTC

RUN \
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
  yum clean all

# Create python virtual environment and install dependencies
COPY requirements.txt /opt/mozdef/envs/mozdef/requirements.txt

USER mozdef
RUN \
  virtualenv /opt/mozdef/envs/python && \
  source /opt/mozdef/envs/python/bin/activate && \
  pip install -r /opt/mozdef/envs/mozdef/requirements.txt

COPY lib /opt/mozdef/envs/mozdef/lib

USER root
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef

WORKDIR /opt/mozdef/envs/mozdef