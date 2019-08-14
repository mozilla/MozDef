# Copyright 2018 Regents of the University of Michigan

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Vendored and modified from https://github.com/zmap/celerybeat-mongo

import datetime

from .periodic_task import PeriodicTask
from .alert_schedule_entry import AlertScheduleEntry
from .celery_rest_client import CeleryRestClient

from celery.beat import Scheduler


class AlertScheduler(Scheduler):

    #: how often should we sync in schedule information
    #: from the backend mongo database
    UPDATE_INTERVAL = datetime.timedelta(seconds=5)

    Entry = AlertScheduleEntry

    Model = PeriodicTask

    def __init__(self, *args, **kwargs):
        self._schedule = {}
        self._last_updated = None
        Scheduler.__init__(self, *args, **kwargs)
        self.max_interval = (kwargs.get('max_interval') or self.app.conf.CELERYBEAT_MAX_LOOP_INTERVAL or 5)
        self.celery_rest = CeleryRestClient()
        self.celery_rest.print_schedule()

    def setup_schedule(self):
        pass

    def requires_update(self):
        """check whether we should pull an updated schedule
        from the backend database"""
        if not self._last_updated:
            return True
        return self._last_updated + self.UPDATE_INTERVAL < datetime.datetime.now()

    @property
    def schedule(self):
        if self.requires_update():
            self._schedule = self.fetch_schedule()
            self._last_updated = datetime.datetime.now()
        return self._schedule

    def fetch_schedule(self):
        api_results = self.celery_rest.fetch_schedule_dict()
        schedule = {}
        for name, doc in api_results.items():
            schedule[name] = self.Entry(doc)
        return schedule
