FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

ARG BOT_TYPE

RUN install --owner mozdef --group mozdef --directory /opt/mozdef/envs/mozdef/bot

COPY --chown=mozdef:mozdef bot/$BOT_TYPE /opt/mozdef/envs/mozdef/bot/$BOT_TYPE
COPY --chown=mozdef:mozdef docker/compose/mozdef_bot/files/mozdefbot.conf /opt/mozdef/envs/mozdef/bot/$BOT_TYPE/mozdefbot.conf

WORKDIR /opt/mozdef/envs/mozdef/bot/$BOT_TYPE

USER mozdef
