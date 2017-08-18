FROM mozdef_base:latest

RUN \
  mkdir /opt/mozdef/envs/mozdef/config && \
  mkdir -p /opt/mozdef/envs/mozdef/docker/conf

COPY docker/conf/initial_setup.py /opt/mozdef/envs/mozdef/docker/conf/initial_setup.py
COPY config/defaultMappingTemplate.json /opt/mozdef/envs/mozdef/config/defaultMappingTemplate.json

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/

WORKDIR /opt/mozdef/envs/mozdef

USER mozdef
