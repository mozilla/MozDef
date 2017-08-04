FROM mozdef_base:latest

COPY mq /opt/mozdef/envs/mozdef/mq
COPY docker/compose/mozdef_mq_syslog/files/syslog_worker.conf /opt/mozdef/envs/mozdef/mq/syslog_worker.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/mq

USER mozdef
