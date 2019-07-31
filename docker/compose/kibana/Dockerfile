FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

# When changing the kibana version, we'll need to update https://github.com/mozilla/MozDef/blob/master/docker/compose/mozdef_bootstrap/files/initial_setup.py accordingly
ENV KIBANA_VERSION 6.8.0

RUN \
  mkdir /kibana && \
  curl --silent --location https://artifacts.elastic.co/downloads/kibana/kibana-$KIBANA_VERSION-linux-x86_64.tar.gz \
    | tar --extract --gzip --strip 1 --directory /kibana

COPY docker/compose/kibana/files/kibana.yml /kibana/config/kibana.yml

WORKDIR /kibana

EXPOSE 5601
