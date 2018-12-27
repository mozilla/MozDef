FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

# When changing kibana version remember to edit
# docker/compose/mozdef_bootstrap/files/initial_setup.py accordingly
ENV KIBANA_VERSION 5.6.7

RUN \
    curl -s -L https://artifacts.elastic.co/downloads/kibana/kibana-$KIBANA_VERSION-linux-x86_64.tar.gz | tar -C / -xz && \
    cd /kibana-$KIBANA_VERSION-linux-x86_64

COPY docker/compose/kibana/files/kibana.yml /kibana-$KIBANA_VERSION-linux-x86_64/config/kibana.yml

WORKDIR /kibana-$KIBANA_VERSION-linux-x86_64

EXPOSE 5601
