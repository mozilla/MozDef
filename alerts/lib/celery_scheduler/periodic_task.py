# Copyright 2013 Regents of the University of Michigan

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

import datetime
import celery.schedules
from bson.objectid import ObjectId

from mozdef_util.utilities.toUTC import toUTC


class Interval():
    def __init__(self, every, period):
        self.every = every
        self.period = period

    @property
    def schedule(self):
        return celery.schedules.schedule(datetime.timedelta(**{self.period: self.every}))

    @property
    def period_singular(self):
        return self.period[:-1]

    def to_dict(self):
        return {
            "every": self.every,
            "period": self.period
        }

    def to_str(self):
        return "{0} {1}".format(
            self.every,
            self.period
        )


class Crontab():
    def __init__(self, minute, hour, day_of_week, day_of_month, month_of_year):
        self.minute = minute
        self.hour = hour
        self.day_of_week = day_of_week
        self.day_of_month = day_of_month
        self.month_of_year = month_of_year

    @property
    def schedule(self):
        return celery.schedules.crontab(
            minute=self.minute,
            hour=self.hour,
            day_of_week=self.day_of_week,
            day_of_month=self.day_of_month,
            month_of_year=self.month_of_year
        )

    def to_dict(self):
        return {
            "minute": self.minute,
            "hour": self.hour,
            "day_of_week": self.day_of_week,
            "day_of_month": self.day_of_month,
            "month_of_year": self.month_of_year,
        }

    def to_str(self):
        return "{0} {1} {2} {3} {4}".format(
            self.minute,
            self.hour,
            self.day_of_week,
            self.day_of_month,
            self.month_of_year
        )


class PeriodicTask():

    def __init__(
            self,
            name,
            task,
            enabled,
            _id=None,
            _cls='PeriodicTask',
            args=[],
            kwargs={},
            celery_schedule=None,
            schedule_type=None,
            schedule_str=None,
            expires=None,
            queue=None,
            exchange=None,
            routing_key=None,
            last_run_at=None,
            run_immediately=False,
            total_run_count=0,
            modifiedat=None,
            modifiedby=None):

        if _id is None:
            _id = str(ObjectId())
        self._id = _id

        self._cls = _cls

        self.name = name
        self.task = task
        self.args = args
        self.kwargs = kwargs

        self.enabled = enabled

        self.expires = expires
        self.queue = queue
        self.exchange = exchange
        self.routing_key = routing_key
        if last_run_at is not None:
            last_run_at = toUTC(last_run_at)
        self.last_run_at = last_run_at
        self.run_immediately = run_immediately
        self.total_run_count = total_run_count

        self.set_schedule(schedule_type, celery_schedule)

    def set_schedule(self, schedule_type, celery_schedule):
        self.schedule_type = schedule_type
        if self.schedule_type == 'interval':
            self.celery_schedule = Interval(**celery_schedule)
        elif self.schedule_type == 'crontab':
            self.celery_schedule = Crontab(**celery_schedule)
        else:
            raise Exception("must define interval or crontab schedule")
        self.schedule_str = self.celery_schedule.to_str()

    @property
    def schedule(self):
        if self.schedule_type == 'interval':
            return self.celery_schedule.schedule
        elif self.schedule_type == 'crontab':
            return self.celery_schedule.schedule
        else:
            raise Exception("must define interval or crontab schedule")

    def to_dict(self):
        last_run_at = self.last_run_at
        if isinstance(self.last_run_at, datetime.datetime):
            last_run_at = last_run_at.isoformat()
        return {
            "name": self.name,
            "task": self.task,
            "enabled": self.enabled,
            "_id": self._id,
            "_cls": self._cls,
            "args": self.args,
            "kwargs": self.kwargs,
            "celery_schedule": self.celery_schedule.to_dict(),
            "schedule_str": self.schedule_str,
            "schedule_type": self.schedule_type,
            "expires": self.expires,
            "queue": self.queue,
            "exchange": self.exchange,
            "routing_key": self.routing_key,
            "last_run_at": last_run_at,
            "run_immediately": self.run_immediately,
            "total_run_count": self.total_run_count,
        }
