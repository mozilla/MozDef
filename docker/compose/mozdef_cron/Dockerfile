FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

RUN \
  yum makecache fast && \
  yum install -y cronie && \
  yum clean all && \
  rm -rf /var/cache/yum

COPY --chown=mozdef:mozdef cron /opt/mozdef/envs/mozdef/cron
COPY docker/compose/mozdef_cron/files/cron_entries.txt /cron_entries.txt

# Copy config files for crons
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/pruneIndexes.conf /opt/mozdef/envs/mozdef/cron/pruneIndexes.conf
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/rotateIndexes.conf /opt/mozdef/envs/mozdef/cron/rotateIndexes.conf
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/eventStats.conf /opt/mozdef/envs/mozdef/cron/eventStats.conf
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/healthAndStatus.conf /opt/mozdef/envs/mozdef/cron/healthAndStatus.conf
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/healthToMongo.conf /opt/mozdef/envs/mozdef/cron/healthToMongo.conf
COPY --chown=mozdef:mozdef docker/compose/mozdef_cron/files/syncAlertsToMongo.conf /opt/mozdef/envs/mozdef/cron/syncAlertsToMongo.conf

# https://stackoverflow.com/a/48651061/168874
COPY docker/compose/mozdef_cron/files/launch_cron /launch_cron

USER mozdef
RUN crontab /cron_entries.txt

USER root
WORKDIR /
CMD ['./launch_cron']
