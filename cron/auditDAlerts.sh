#!/usr/bin/env bash
source  /home/mozdef/envs/mozdef/bin/activate
/home/mozdef/envs/mozdef/cron/auditDAlerts.py -c /home/mozdef/envs/mozdef/cron/auditDAlerts.conf
/home/mozdef/envs/mozdef/cron/auditDFileAlerts.py -c /home/mozdef/envs/mozdef/cron/auditDAlerts.conf
