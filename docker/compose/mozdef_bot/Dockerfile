FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

ARG BOT_TYPE

COPY bot/$BOT_TYPE /opt/mozdef/envs/mozdef/bot/$BOT_TYPE
COPY docker/compose/mozdef_bot/files/mozdefbot.conf /opt/mozdef/envs/mozdef/bot/$BOT_TYPE/mozdefbot.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/bot/$BOT_TYPE

WORKDIR /opt/mozdef/envs/mozdef/bot/$BOT_TYPE

USER mozdef

CMD ["/wait-for-port.sh", "rabbitmq:5672", "python", "mozdefbot.py", "-c", "mozdefbot.conf"]
