# Copyright 2013 Regents of the University of Michigan

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Vendored and modified from https://github.com/zmap/celerybeat-mongo

from celery.beat import Scheduler, ScheduleEntry
from celery import current_app


class AlertScheduleEntry(ScheduleEntry):

    def __init__(self, task):
        self._task = task

        self.app = current_app._get_current_object()
        self.name = self._task.name
        self.task = self._task.task

        self.enabled = self._task.enabled
        self.schedule_str = self._task.schedule_str
        self.schedule_type = self._task.schedule_type
        self.schedule = self._task.schedule

        self.args = self._task.args
        self.kwargs = self._task.kwargs
        self.options = {
            'queue': self._task.queue,
            'exchange': self._task.exchange,
            'routing_key': self._task.routing_key,
            'expires': self._task.expires
        }
        if self._task.total_run_count is None:
            self._task.total_run_count = 0
        self.total_run_count = self._task.total_run_count

        if not self._task.last_run_at:
            self.last_run_at = self._default_now()
        else:
            self.last_run_at = self._task.last_run_at

    def _default_now(self):
        return self.app.now()

    def next(self):
        self._task.last_run_at = self.app.now()
        self._task.total_run_count += 1
        self._task.run_immediately = False
        return self.__class__(self._task)

    __next__ = next

    def is_due(self):
        if not self._task.enabled:
            return False, 5.0   # 5 second delay for re-enable.
        if self._task.run_immediately:
            # figure out when the schedule would run next anyway
            _, n = self.schedule.is_due(self.last_run_at)
            return True, n
        return self.schedule.is_due(self.last_run_at)

    def __repr__(self):
        return '<AlertScheduleEntry ({0} {1}(*{2}, **{3}) {{4}})>'.format(
            self.name, self.task, self.args,
            self.kwargs, self.schedule,
        )

    def reserve(self, entry):
        new_entry = Scheduler.reserve(self, entry)
        return new_entry

    def update(self):
        if self.total_run_count > self._task.total_run_count:
            self._task.total_run_count = self.total_run_count
        if self.last_run_at and self._task.last_run_at and self.last_run_at > self._task.last_run_at:
            self._task.last_run_at = self.last_run_at
        self._task.run_immediately = False
