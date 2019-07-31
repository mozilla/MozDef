FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY --chown=mozdef:mozdef alerts /opt/mozdef/envs/mozdef/alerts
COPY --chown=mozdef:mozdef docker/compose/mozdef_alerts/files/config.py /opt/mozdef/envs/mozdef/alerts/lib/
COPY --chown=mozdef:mozdef docker/compose/mozdef_alerts/files/get_watchlist.conf /opt/mozdef/envs/mozdef/alerts/get_watchlist.conf

WORKDIR /opt/mozdef/envs/mozdef/alerts

USER mozdef
