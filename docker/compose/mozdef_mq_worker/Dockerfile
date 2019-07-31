FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY --chown=mozdef:mozdef mq /opt/mozdef/envs/mozdef/mq
COPY --chown=mozdef:mozdef docker/compose/mozdef_mq_worker/files/*.conf /opt/mozdef/envs/mozdef/mq/

WORKDIR /opt/mozdef/envs/mozdef/mq

USER mozdef
