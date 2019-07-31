FROM centos:7

LABEL maintainer="mozdef@mozilla.com"

ENV ES_VERSION 6.8.0
ENV ES_JAVA_VERSION 1.8.0


RUN \
  gpg="gpg --no-default-keyring --secret-keyring /dev/null --keyring /dev/null --no-option --keyid-format 0xlong" && \
  rpmkeys --import /etc/pki/rpm-gpg/RPM-GPG-KEY-CentOS-7 && \
  rpm -qi gpg-pubkey-f4a80eb5 | $gpg | grep 0x24C6A8A7F4A80EB5 && \
  rpmkeys --import https://packages.elastic.co/GPG-KEY-elasticsearch && \
  rpm -qi gpg-pubkey-d88e42b4-52371eca | $gpg | grep 0xD27D666CD88E42B4 && \
  yum install -y java-$ES_JAVA_VERSION && \
  mkdir -p /opt/mozdef/envs && \
  curl --silent --location https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-$ES_VERSION.rpm -o elasticsearch.rpm && \
  rpm --install elasticsearch.rpm && \
  yum clean all && \
  rm -rf /var/cache/yum

USER elasticsearch

COPY docker/compose/elasticsearch/files/elasticsearch.yml /etc/elasticsearch/elasticsearch.yml
COPY docker/compose/elasticsearch/files/jvm.options /etc/elasticsearch/jvm.options

VOLUME /var/lib/elasticsearch

WORKDIR /usr/share/elasticsearch

EXPOSE 9200
