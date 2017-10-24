FROM mozdef_base:latest

COPY alerts /opt/mozdef/envs/mozdef/alerts
COPY docker/compose/mozdef_alertplugins/files/alert_worker.conf /opt/mozdef/envs/mozdef/alerts/alert_worker.conf
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/alerts

WORKDIR /opt/mozdef/envs/mozdef/alerts

USER mozdef
