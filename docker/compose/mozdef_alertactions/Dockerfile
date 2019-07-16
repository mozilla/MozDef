FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY --chown=mozdef:mozdef alerts /opt/mozdef/envs/mozdef/alerts
COPY --chown=mozdef:mozdef docker/compose/mozdef_alertactions/files/alert_actions_worker.conf /opt/mozdef/envs/mozdef/alerts/alert_actions_worker.conf
COPY --chown=mozdef:mozdef docker/compose/mozdef_alerts/files/config.py /opt/mozdef/envs/mozdef/alerts/lib/config.py

WORKDIR /opt/mozdef/envs/mozdef/alerts

USER mozdef
