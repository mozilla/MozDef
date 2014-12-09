#!/usr/bin/env bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# Copyright (c) 2014 Mozilla Corporation
#
# Contributors:
# Jeff Bryner jbryner@mozilla.com

source  /home/mozdef/envs/mozdef/bin/activate
/home/mozdef/envs/mozdef/cron/healthAndStatus.py -c /home/mozdef/envs/mozdef/cron/healthAndStatus.conf
/home/mozdef/envs/mozdef/cron/healthToMongo.py -c /home/mozdef/envs/mozdef/cron/healthToMongo.conf
/home/mozdef/envs/mozdef/cron/eventStats.py -c /home/mozdef/envs/mozdef/cron/eventStats.conf
