FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY mq /opt/mozdef/envs/mozdef/mq
COPY docker/compose/mozdef_mq_worker/files/esworker_eventtask.conf /opt/mozdef/envs/mozdef/mq/esworker_eventtask.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/mq

WORKDIR /opt/mozdef/envs/mozdef/mq

USER mozdef
