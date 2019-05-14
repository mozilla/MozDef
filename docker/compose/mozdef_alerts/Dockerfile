FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY alerts /opt/mozdef/envs/mozdef/alerts
COPY docker/compose/mozdef_alerts/files/config.py /opt/mozdef/envs/mozdef/alerts/lib/
COPY docker/compose/mozdef_alerts/files/get_watchlist.conf /opt/mozdef/envs/mozdef/alerts/get_watchlist.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/alerts

WORKDIR /opt/mozdef/envs/mozdef/alerts

USER mozdef
