# Copyright 2018 Regents of the University of Michigan

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0

# Vendored from https://github.com/zmap/celerybeat-mongo

import datetime
from mongoengine import *
from celery import current_app
import celery.schedules


def get_periodic_task_collection():
    if hasattr(current_app.conf, "CELERY_MONGODB_SCHEDULER_COLLECTION") \
            and current_app.conf.CELERY_MONGODB_SCHEDULER_COLLECTION:
        return current_app.conf.CELERY_MONGODB_SCHEDULER_COLLECTION
    return "schedules"


#: Authorized values for PeriodicTask.Interval.period
PERIODS = ('days', 'hours', 'minutes', 'seconds', 'microseconds')


class PeriodicTask(DynamicDocument):
    """mongo database model that represents a periodic task"""

    meta = {'collection': get_periodic_task_collection(),
            'allow_inheritance': True}

    class Interval(EmbeddedDocument):
        meta = {'allow_inheritance': True}

        every = IntField(min_value=0, default=0, required=True)
        period = StringField(choices=PERIODS)

        @property
        def schedule(self):
            return celery.schedules.schedule(datetime.timedelta(**{self.period: self.every}))

        @property
        def period_singular(self):
            return self.period[:-1]

        def __unicode__(self):
            if self.every == 1:
                return 'every {0.period_singular}'.format(self)
            return 'every {0.every} {0.period}'.format(self)

    class Crontab(EmbeddedDocument):
        meta = {'allow_inheritance': True}

        minute = StringField(default='*', required=True)
        hour = StringField(default='*', required=True)
        day_of_week = StringField(default='*', required=True)
        day_of_month = StringField(default='*', required=True)
        month_of_year = StringField(default='*', required=True)

        @property
        def schedule(self):
            return celery.schedules.crontab(minute=self.minute,
                                     hour=self.hour,
                                     day_of_week=self.day_of_week,
                                     day_of_month=self.day_of_month,
                                     month_of_year=self.month_of_year)

        def __unicode__(self):
            rfield = lambda f: f and str(f).replace(' ', '') or '*'
            return '{0} {1} {2} {3} {4} (m/h/d/dM/MY)'.format(
                rfield(self.minute), rfield(self.hour), rfield(self.day_of_week),
                rfield(self.day_of_month), rfield(self.month_of_year),
            )

    name = StringField(unique=True)
    task = StringField(required=True)

    interval = EmbeddedDocumentField(Interval)
    crontab = EmbeddedDocumentField(Crontab)

    args = ListField()
    kwargs = DictField()

    queue = StringField()
    exchange = StringField()
    routing_key = StringField()
    soft_time_limit = IntField()

    expires = DateTimeField()
    start_after = DateTimeField()
    enabled = BooleanField(default=False)

    last_run_at = DateTimeField()

    total_run_count = IntField(min_value=0, default=0)
    max_run_count = IntField(min_value=0, default=0)

    date_changed = DateTimeField()
    description = StringField()

    run_immediately = BooleanField()

    #objects = managers.PeriodicTaskManager()
    no_changes = False

    def clean(self):
        """validation by mongoengine to ensure that you only have
        an interval or crontab schedule, but not both simultaneously"""
        if self.interval and self.crontab:
            msg = 'Cannot define both interval and crontab schedule.'
            raise ValidationError(msg)
        if not (self.interval or self.crontab):
            msg = 'Must defined either interval or crontab schedule.'
            raise ValidationError(msg)

    @property
    def schedule(self):
        if self.interval:
            return self.interval.schedule
        elif self.crontab:
            return self.crontab.schedule
        else:
            raise Exception("must define interval or crontab schedule")

    def __unicode__(self):
        fmt = '{0.name}: {{no schedule}}'
        if self.interval:
            fmt = '{0.name}: {0.interval}'
        elif self.crontab:
            fmt = '{0.name}: {0.crontab}'
        else:
            raise Exception("must define interval or crontab schedule")
        return fmt.format(self)
