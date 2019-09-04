# Copyright 2013 Regents of the University of Michigan

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Vendored and modified from https://github.com/zmap/celerybeat-mongo

import datetime

from celery.beat import Scheduler
from celery.utils.log import get_logger
from .alert_schedule_entry import AlertScheduleEntry

from .periodic_task import PeriodicTask
from .celery_rest_client import CeleryRestClient


class AlertsScheduler(Scheduler):

    #: how often should we sync in schedule information
    #: from the backend mongo database
    UPDATE_INTERVAL = datetime.timedelta(seconds=5)

    Entry = AlertScheduleEntry

    # The same as the web ui
    SCHEDULER_DB = "meteor"

    def __init__(self, *args, **kwargs):
        self._schedule = {}
        self._last_updated = None
        Scheduler.__init__(self, *args, **kwargs)
        self.max_interval = (kwargs.get('max_interval') or self.app.conf.CELERYBEAT_MAX_LOOP_INTERVAL or 5)
        self.celery_rest = CeleryRestClient()
        self._schedule = self.get_from_api()
        self.print_schedule()

    def print_schedule(self):
        get_logger(__name__).info("**** Current Alert Schedule ****")
        for name, schedule in self._schedule.items():
            get_logger(__name__).info("\t{0}: {1} {2}".format(name, schedule.schedule_type, schedule.schedule_str))
        if len(self._schedule) == 0:
            get_logger(__name__).info("\tNo alerts are currently enabled.")

    def setup_schedule(self):
        pass

    def requires_update(self):
        """check whether we should pull an updated schedule
        from the backend database"""
        if not self._last_updated:
            return True
        return self._last_updated + self.UPDATE_INTERVAL < datetime.datetime.now()

    def get_from_api(self):
        try:
            d = {}
            api_results = self.celery_rest.fetch_schedule_dict()
            for name, doc in api_results.items():
                if doc['enabled']:
                    d[name] = self.Entry(PeriodicTask(**doc))
            return d
        except Exception as e:
            get_logger(__name__).error("Received exception when fetching schedule: {0}".format(e))
            return self._schedule

    def schedules_equal(self, old_schedules, new_schedules):
        result = super().schedules_equal(old_schedules, new_schedules)
        if result is False:
            get_logger(__name__).info("Updating current alert schedule with new schedule")
            self.print_schedule()
        return result

    @property
    def schedule(self):
        if self.requires_update():
            self.sync()
            self._schedule = self.get_from_api()
            self._last_updated = datetime.datetime.now()
        return self._schedule

    def sync(self):
        for entry in self._schedule.values():
            entry.update()
        dict_schedule = {}
        for name, alert_schedule in self._schedule.items():
            dict_schedule[name] = alert_schedule._task.to_dict()
        try:
            self.celery_rest.sync_schedules(dict_schedule)
        except Exception as e:
            get_logger(__name__).error("Received exception during sync_schedules: {0}".format(e))
