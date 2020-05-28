FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY --chown=mozdef:mozdef cron/mozdefStateDefaultMappingTemplate.json /opt/mozdef/envs/mozdef/cron/mozdefStateDefaultMappingTemplate.json
COPY --chown=mozdef:mozdef cron/defaultMappingTemplate.json /opt/mozdef/envs/mozdef/cron/defaultMappingTemplate.json
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/rotateIndexes.conf /opt/mozdef/envs/mozdef/cron/rotateIndexes.conf

COPY --chown=mozdef:mozdef scripts/setup /opt/mozdef/envs/mozdef/scripts/setup

WORKDIR /opt/mozdef/envs/mozdef/scripts/setup

USER mozdef
