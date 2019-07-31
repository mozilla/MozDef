FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

COPY --chown=mozdef:mozdef rest /opt/mozdef/envs/mozdef/rest
COPY --chown=mozdef:mozdef docker/compose/mozdef_rest/files/index.conf /opt/mozdef/envs/mozdef/rest/index.conf

EXPOSE 8081

WORKDIR /opt/mozdef/envs/mozdef/rest

USER mozdef
