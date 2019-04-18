FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY mq /opt/mozdef/envs/mozdef/mq
COPY docker/compose/mozdef_mq_worker/files/*.conf /opt/mozdef/envs/mozdef/mq/

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/mq

WORKDIR /opt/mozdef/envs/mozdef/mq

USER mozdef
