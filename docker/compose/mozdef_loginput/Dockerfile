FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY loginput /opt/mozdef/envs/mozdef/loginput
COPY docker/compose/mozdef_loginput/files/index.conf /opt/mozdef/envs/mozdef/loginput/index.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/loginput

EXPOSE 8080

WORKDIR /opt/mozdef/envs/mozdef/loginput

USER mozdef
