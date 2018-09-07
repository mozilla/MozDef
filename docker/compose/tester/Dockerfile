FROM base:latest

COPY tests /opt/mozdef/envs/mozdef/tests
COPY alerts /opt/mozdef/envs/mozdef/alerts
COPY mq /opt/mozdef/envs/mozdef/mq
COPY loginput /opt/mozdef/envs/mozdef/loginput
COPY rest /opt/mozdef/envs/mozdef/rest
COPY cron /opt/mozdef/envs/mozdef/cron

COPY docker/compose/tester/files/tests_config.conf /opt/mozdef/envs/mozdef/tests/config.conf
COPY docker/compose/tester/files/loginput_config.conf /opt/mozdef/envs/mozdef/loginput/index.conf
COPY docker/compose/tester/files/rest_config.conf /opt/mozdef/envs/mozdef/rest/index.conf

USER root

RUN \
  source /opt/mozdef/envs/python/bin/activate && \
  pip install -r /opt/mozdef/envs/mozdef/tests/requirements_tests.txt
