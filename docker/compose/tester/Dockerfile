FROM mozdef/mozdef_base

COPY tests /opt/mozdef/envs/mozdef/tests
RUN pip install -r /opt/mozdef/envs/mozdef/tests/requirements_tests.txt

COPY alerts /opt/mozdef/envs/mozdef/alerts
COPY bot /opt/mozdef/envs/mozdef/bot
COPY cron /opt/mozdef/envs/mozdef/cron
COPY scripts /opt/mozdef/envs/mozdef/scripts
COPY loginput /opt/mozdef/envs/mozdef/loginput
COPY mozdef_util /opt/mozdef/envs/mozdef/mozdef_util
COPY mq /opt/mozdef/envs/mozdef/mq
COPY rest /opt/mozdef/envs/mozdef/rest
COPY .flake8 /opt/mozdef/envs/mozdef/.flake8

COPY docker/compose/tester/files/tests_config.conf /opt/mozdef/envs/mozdef/tests/config.conf
COPY docker/compose/tester/files/loginput_index.conf /opt/mozdef/envs/mozdef/tests/loginput/index.conf
COPY docker/compose/tester/files/rest_index.conf /opt/mozdef/envs/mozdef/tests/rest/index.conf

