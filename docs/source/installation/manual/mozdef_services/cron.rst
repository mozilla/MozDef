Cron
****

Crontab is used to run periodic maintenance tasks in MozDef.

Recommended mozdef user crontab entries for Alert services::

  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/healthAndStatus.sh
  */15 * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/eventStats.sh
  0 0 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/esMaint.sh
  0 8 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/pruneES.sh
  0 0 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/update_geolite_db.sh
  0 1 * * 0 /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/closeIndices.sh

Recommended mozdef user crontab entries for Ingest services::

  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/healthAndStatus.sh
  #Ansible: update_geolite_db.sh
  0 0 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/update_geolite_db.sh

.. note:: You should run these crontab entries on each ingest host that you have in your MozDef environment.

Recommended mozdef user crontab entries for Web services::

  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/healthToMongo.sh
  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/collectAttackers.sh
  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/syncAlertsToMongo.sh
  0 * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/esCacheMaint.sh