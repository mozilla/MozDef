# Copyright 2018 Regents of the University of Michigan

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Vendored and modified from https://github.com/zmap/celerybeat-mongo

import datetime

from mozdef_util.utilities.toUTC import toUTC
from celery.beat import Scheduler, ScheduleEntry
from celery import current_app
import celery.schedules


class AlertScheduleEntry(ScheduleEntry):

    def __init__(self, task):
        self._task = task

        self.app = current_app._get_current_object()
        self.name = self._task['name']
        self.task = self._task['name']

        # Fill out schedule
        if self._task['schedule_type'] == 'crontab':
            self.schedule = celery.schedules.crontab(
                minute=self._task['crontab']['minute'],
                hour=self._task['crontab']['hour'],
                day_of_week=self._task['crontab']['day_of_week'],
                day_of_month=self._task['crontab']['day_of_month'],
                month_of_year=self._task['crontab']['month_of_year']
            )
        elif self._task['schedule_type'] == 'interval':
            self.schedule = celery.schedules.schedule(datetime.timedelta(**{'seconds': self._task['interval']['every']}))

        self.args = self._task['args']
        self.kwargs = self._task['kwargs']
        self.options = {
            'enabled': self._task['enabled']
        }
        if 'last_run_at' not in self._task:
            self._task['last_run_at'] = self._default_now()
        self.last_run_at = toUTC(self._task['last_run_at'])
        if 'run_immediately' not in self._task:
            self._task['run_immediately'] = False

    def _default_now(self):
        return self.app.now()

    def next(self):
        self._task['last_run_at'] = self.app.now()
        self._task['run_immediately'] = False
        return self.__class__(self._task)

    __next__ = next

    def is_due(self):
        if not self._task['enabled']:
            return False, 5.0   # 5 second delay for re-enable.
        if 'start_after' in self._task and self._task['start_after']:
            if datetime.datetime.now() < self._task['start_after']:
                return False, 5.0
        if self._task['run_immediately']:
            # figure out when the schedule would run next anyway
            _, n = self.schedule.is_due(self.last_run_at)
            return True, n
        return self.schedule.is_due(self.last_run_at)

    def __repr__(self):
        return (u'<{0} ({1} {2}(*{3}, **{4}) {{5}})>'.format(
            self.__class__.__name__,
            self.name, self.task, self.args,
            self.kwargs, self.schedule,
        ))

    def reserve(self, entry):
        new_entry = Scheduler.reserve(self, entry)
        return new_entry
