FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY mq /opt/mozdef/envs/mozdef/mq
COPY docker/compose/mozdef_mq_worker/files/*.conf /opt/mozdef/envs/mozdef/mq/

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/mq

WORKDIR /opt/mozdef/envs/mozdef/mq

USER mozdef

CMD ["/wait-for-container.sh", "bootstrap", "python", "esworker_eventtask.py", "-c", "esworker_eventtask.conf"]
