import json
from alerts.lib.celery_scheduler.periodic_task import PeriodicTask, Crontab, Interval
from celery.schedules import schedule as celery_sched
from celery.schedules import crontab as celery_crontab

from datetime import datetime


class TestIntervalPeriodicTask():
    def setup(self):
        self.task_dict = {
            '_id': '5d685905d8888b2fc919189a',
            '_cls': 'PeriodicTask',
            'args': [],
            'enabled': True,
            'celery_schedule': {
                'every': 1.0,
                'period': 'seconds'
            },
            'schedule_type': 'interval',
            'kwargs': {},
            'name': 'bruteforce_ssh.AlertBruteforceSsh',
            'task': 'bruteforce_ssh.AlertBruteforceSsh'
        }

    def test_parsing_dict(self):
        task = PeriodicTask(**self.task_dict)
        assert task.name == 'bruteforce_ssh.AlertBruteforceSsh'
        assert task.task == 'bruteforce_ssh.AlertBruteforceSsh'
        assert isinstance(task._id, str)
        assert task.args == []
        assert task.kwargs == {}
        assert task.enabled is True
        assert task.queue is None
        assert task.exchange is None
        assert task.routing_key is None
        assert task.last_run_at is None
        assert task.run_immediately is False
        assert task.total_run_count is 0
        assert task.schedule_type == 'interval'
        assert task.schedule_str == '1.0 seconds'
        assert isinstance(task.celery_schedule, Interval) is True
        assert isinstance(task.schedule, celery_sched) is True

    def test_to_dict(self):
        expected_dict = {
            '_cls': 'PeriodicTask',
            '_id': '5d685905d8888b2fc919189a',
            'args': [],
            'celery_schedule': {'every': 1.0, 'period': 'seconds'},
            'enabled': True,
            'exchange': None,
            'expires': None,
            'kwargs': {},
            'last_run_at': None,
            'name': 'bruteforce_ssh.AlertBruteforceSsh',
            'queue': None,
            'routing_key': None,
            'run_immediately': False,
            'schedule_str': '1.0 seconds',
            'schedule_type': 'interval',
            'task': 'bruteforce_ssh.AlertBruteforceSsh',
            'total_run_count': 0
        }
        task = PeriodicTask(**self.task_dict)
        assert task.to_dict() == expected_dict


class TestCrontabPeriodicTask():
    def setup(self):
        self.task_dict = {
            '_cls': 'PeriodicTask',
            '_id': '5d685905d8888b2fc919189a',
            'args': [],
            'enabled': True,
            'celery_schedule': {
                'minute': 0,
                'hour': 5,
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
            },
            'schedule_type': 'crontab',
            'kwargs': {},
            'name': 'bruteforce_ssh.AlertBruteforceSsh',
            'task': 'bruteforce_ssh.AlertBruteforceSsh'
        }

    def test_parsing_dict(self):
        task = PeriodicTask(**self.task_dict)
        assert task.name == 'bruteforce_ssh.AlertBruteforceSsh'
        assert task.task == 'bruteforce_ssh.AlertBruteforceSsh'
        assert task.args == []
        assert task.kwargs == {}
        assert task.enabled is True
        assert task.queue is None
        assert task.exchange is None
        assert task.routing_key is None
        assert task.last_run_at is None
        assert task.run_immediately is False
        assert task.total_run_count is 0
        assert task.schedule_type == 'crontab'
        assert task.schedule_str == '0 5 * * *'
        assert isinstance(task.celery_schedule, Crontab) is True
        assert isinstance(task.schedule, celery_crontab) is True

    def test_to_dict(self):
        expected_dict = {
            '_cls': 'PeriodicTask',
            '_id': '5d685905d8888b2fc919189a',
            'args': [],
            'enabled': True,
            'exchange': None,
            'expires': None,
            'kwargs': {},
            'last_run_at': None,
            'name': 'bruteforce_ssh.AlertBruteforceSsh',
            'queue': None,
            'routing_key': None,
            'run_immediately': False,
            'schedule_type': 'crontab',
            'celery_schedule': {
                'day_of_month': '*',
                'day_of_week': '*',
                'hour': 5,
                'minute': 0,
                'month_of_year': '*'},
            'schedule_str': '0 5 * * *',
            'task': 'bruteforce_ssh.AlertBruteforceSsh',
            'total_run_count': 0
        }
        task = PeriodicTask(**self.task_dict)
        assert task.to_dict() == expected_dict

    def test_can_json(self):
        task = PeriodicTask(**self.task_dict)
        assert json.dumps(task.to_dict())


class TestLastRunPeriodicTask():
    def setup(self):
        self.task_dict = {
            '_cls': 'PeriodicTask',
            '_id': '5d685905d8888b2fc919189a',
            'args': [],
            'enabled': True,
            'celery_schedule': {
                'minute': 0,
                'hour': 5,
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
            },
            'schedule_type': 'crontab',
            'kwargs': {},
            'name': 'bruteforce_ssh.AlertBruteforceSsh',
            'task': 'bruteforce_ssh.AlertBruteforceSsh',
            'last_run_at': '2019-08-30T19:39:10.773686+00:00',
        }

    def test_parsing_dict(self):
        task = PeriodicTask(**self.task_dict)
        assert isinstance(task.last_run_at, datetime)

    def test_to_dict(self):
        expected_dict = {
            '_cls': 'PeriodicTask',
            '_id': '5d685905d8888b2fc919189a',
            'args': [],
            'enabled': True,
            'exchange': None,
            'expires': None,
            'kwargs': {},
            'last_run_at': '2019-08-30T19:39:10.773686+00:00',
            'name': 'bruteforce_ssh.AlertBruteforceSsh',
            'queue': None,
            'routing_key': None,
            'run_immediately': False,
            'schedule_type': 'crontab',
            'celery_schedule': {
                'day_of_month': '*',
                'day_of_week': '*',
                'hour': 5,
                'minute': 0,
                'month_of_year': '*'},
            'schedule_str': '0 5 * * *',
            'task': 'bruteforce_ssh.AlertBruteforceSsh',
            'total_run_count': 0
        }
        task = PeriodicTask(**self.task_dict)
        assert task.to_dict() == expected_dict

    def test_can_json(self):
        task = PeriodicTask(**self.task_dict)
        assert json.dumps(task.to_dict())


class TestIDPeriodicTask():
    def setup(self):
        self.task_dict = {
            '_cls': 'PeriodicTask',
            'args': [],
            'enabled': True,
            'celery_schedule': {
                'every': 1.0,
                'period': 'seconds'
            },
            'schedule_type': 'interval',
            'kwargs': {},
            'name': 'bruteforce_ssh.AlertBruteforceSsh',
            'task': 'bruteforce_ssh.AlertBruteforceSsh'
        }

    def test_parsing_dict(self):
        task = PeriodicTask(**self.task_dict)
        assert isinstance(task._id, str)

    def test_to_dict(self):
        task = PeriodicTask(**self.task_dict)
        assert isinstance(task.to_dict()['_id'], str)
