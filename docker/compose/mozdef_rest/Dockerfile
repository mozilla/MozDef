FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY rest /opt/mozdef/envs/mozdef/rest
COPY docker/compose/mozdef_rest/files/index.conf /opt/mozdef/envs/mozdef/rest/index.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/rest

EXPOSE 8081

WORKDIR /opt/mozdef/envs/mozdef/rest

USER mozdef
