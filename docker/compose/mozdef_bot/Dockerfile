FROM mozdef_base:latest

LABEL maintainer="mozdef@mozilla.com"

COPY bot /opt/mozdef/envs/mozdef/bot
COPY docker/compose/mozdef_bot/files/mozdefbot.conf /opt/mozdef/envs/mozdef/bot/mozdefbot.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/bot

WORKDIR /opt/mozdef/envs/mozdef/bot

USER mozdef
