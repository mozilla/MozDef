Cron
****

Crontab is used to run periodic maintenance tasks in MozDef.

MozDef cron entries can be broken up similarly to the 3 Service Groups (Alerts, Ingest, Web).

.. note:: You should run the Ingest Related Tasks on each ingest host that you have in your MozDef environment.


Recommended Mozdef Crontab::

  su mozdef
  crontab -e

With the following contents::

  ## Alert Related Tasks ##
  */15 * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/eventStats.sh
  0 0 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/rotateIndexes.sh
  0 8 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/pruneIndexes.sh
  0 0 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/update_geolite_db.sh
  0 1 * * 0 /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/closeIndices.sh

  ## Ingest Related Tasks ##
  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/healthAndStatus.sh
  0 0 * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/update_geolite_db.sh

  ## Web Related Tasks ##
  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/healthToMongo.sh
  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/collectAttackers.sh
  * * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/syncAlertsToMongo.sh
  # Uncomment if running multiple Elasticsearch nodes
  #0 * * * * /opt/mozdef/envs/mozdef/cron/cronic /opt/mozdef/envs/mozdef/cron/esCacheMaint.sh
