FROM mozdef_base:latest

COPY alerts /opt/mozdef/envs/mozdef/alerts
COPY docker/compose/mozdef_alertplugins/files/alertWorker.conf /opt/mozdef/envs/mozdef/alerts/alertWorker.conf
RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/alerts

WORKDIR /opt/mozdef/envs/mozdef/alerts

USER mozdef
