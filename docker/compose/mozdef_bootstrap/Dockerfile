FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

RUN install --owner mozdef --group mozdef --directory /opt/mozdef/envs/mozdef/docker /opt/mozdef/envs/mozdef/docker/conf

COPY --chown=mozdef:mozdef cron/mozdefStateDefaultMappingTemplate.json /opt/mozdef/envs/mozdef/cron/mozdefStateDefaultMappingTemplate.json
COPY --chown=mozdef:mozdef cron/defaultMappingTemplate.json /opt/mozdef/envs/mozdef/cron/defaultMappingTemplate.json
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/backup.conf /opt/mozdef/envs/mozdef/cron/backup.conf
COPY --chown=mozdef:mozdef docker/compose/mozdef_bootstrap/files/initial_setup.py /opt/mozdef/envs/mozdef/initial_setup.py
COPY --chown=mozdef:mozdef docker/compose/mozdef_bootstrap/files/index_mappings /opt/mozdef/envs/mozdef/index_mappings
COPY --chown=mozdef:mozdef docker/compose/mozdef_bootstrap/files/resources /opt/mozdef/envs/mozdef/resources

WORKDIR /opt/mozdef/envs/mozdef

USER mozdef
