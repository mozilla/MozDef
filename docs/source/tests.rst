Tests
=====

Our test suite builds and runs entirely in `docker`, so a Docker daemon is required to be running locally. The test suite requires a local Elasticsearch and RabbitMQ service to run, but will be started automatically as containers as part of the tests make targets.

Run tests
---------

To run our entire test suite, simply run::

  make tests

If you want to only run a specific test file/directory, you can specify the `TEST_CASE` parameter::

  make tests TEST_CASE=tests/mq/plugins/test_github_webhooks.py

.. note:: If you end up with a clobbered ES index, or anything like that which might end up in failing tests, you can clean the environment with `make clean`. Then run the tests again.

.. _docker: https://www.docker.io/
