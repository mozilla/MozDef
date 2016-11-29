#!/usr/bin/env bash
source  /opt/mozdef/envs/mozdef/bin/activate
/opt/mozdef/envs/mozdef/cron/auditDAlerts.py -c /opt/mozdef/envs/mozdef/cron/auditDAlerts.conf
/opt/mozdef/envs/mozdef/cron/auditDFileAlerts.py -c /opt/mozdef/envs/mozdef/cron/auditDAlerts.conf
