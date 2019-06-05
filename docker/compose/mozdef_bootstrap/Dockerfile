FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

RUN mkdir -p /opt/mozdef/envs/mozdef/docker/conf

COPY cron/mozdefStateDefaultMappingTemplate.json /opt/mozdef/envs/mozdef/cron/mozdefStateDefaultMappingTemplate.json
COPY cron/defaultMappingTemplate.json /opt/mozdef/envs/mozdef/cron/defaultMappingTemplate.json
COPY docker/compose/mozdef_cron/files/backup.conf /opt/mozdef/envs/mozdef/cron/backup.conf
COPY docker/compose/mozdef_bootstrap/files/initial_setup.py /opt/mozdef/envs/mozdef/initial_setup.py
COPY docker/compose/mozdef_bootstrap/files/index_mappings /opt/mozdef/envs/mozdef/index_mappings
COPY docker/compose/mozdef_bootstrap/files/dashboards /opt/mozdef/envs/mozdef/dashboards

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/

WORKDIR /opt/mozdef/envs/mozdef

USER mozdef
