FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY alerts /opt/mozdef/envs/mozdef/alerts
COPY docker/compose/mozdef_alertactions/files/alert_actions_worker.conf /opt/mozdef/envs/mozdef/alerts/alert_actions_worker.conf
COPY docker/compose/mozdef_alerts/files/config.py /opt/mozdef/envs/mozdef/alerts/lib/config.py
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/alerts

WORKDIR /opt/mozdef/envs/mozdef/alerts

USER mozdef
