FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY --chown=mozdef:mozdef loginput /opt/mozdef/envs/mozdef/loginput
COPY --chown=mozdef:mozdef docker/compose/mozdef_loginput/files/index.conf /opt/mozdef/envs/mozdef/loginput/index.conf

EXPOSE 8080

WORKDIR /opt/mozdef/envs/mozdef/loginput

USER mozdef
