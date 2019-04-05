FROM mozdef/mozdef_base

LABEL maintainer="mozdef@mozilla.com"

RUN \
  yum makecache fast && \
  yum install -y cronie && \
  yum clean all

COPY cron /opt/mozdef/envs/mozdef/cron
COPY docker/compose/mozdef_cron/files/cron_entries.txt /cron_entries.txt

# Copy config files for crons
COPY docker/compose/mozdef_cron/files/backup.conf /opt/mozdef/envs/mozdef/cron/backup.conf
COPY docker/compose/mozdef_cron/files/collectAttackers.conf /opt/mozdef/envs/mozdef/cron/collectAttackers.conf
COPY docker/compose/mozdef_cron/files/eventStats.conf /opt/mozdef/envs/mozdef/cron/eventStats.conf
COPY docker/compose/mozdef_cron/files/healthAndStatus.conf /opt/mozdef/envs/mozdef/cron/healthAndStatus.conf
COPY docker/compose/mozdef_cron/files/healthToMongo.conf /opt/mozdef/envs/mozdef/cron/healthToMongo.conf
COPY docker/compose/mozdef_cron/files/syncAlertsToMongo.conf /opt/mozdef/envs/mozdef/cron/syncAlertsToMongo.conf

RUN chown -R mozdef:mozdef /opt/mozdef/envs/mozdef/cron

# https://stackoverflow.com/a/48651061/168874
COPY docker/compose/mozdef_cron/files/launch_cron /launch_cron

USER mozdef
RUN crontab /cron_entries.txt

USER root
WORKDIR /
CMD ['./launch_cron']
