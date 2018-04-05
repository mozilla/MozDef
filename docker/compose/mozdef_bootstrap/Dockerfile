FROM mozdef_base:latest

LABEL maintainer="mozdef@mozilla.com"

RUN mkdir -p /opt/mozdef/envs/mozdef/docker/conf

COPY docker/conf/initial_setup.py /opt/mozdef/envs/mozdef/docker/conf/initial_setup.py
COPY cron/defaultMappingTemplate.json /opt/mozdef/envs/mozdef/cron/defaultMappingTemplate.json

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/

WORKDIR /opt/mozdef/envs/mozdef

USER mozdef
