RabbitMQ
********

`RabbitMQ`_ is used on workers to have queues of events waiting to be inserted into the Elasticsearch cluster (storage).


RabbitMQ requires `EPEL repos`_ so we need to first install that::

  yum  -y install epel-release

Download and install Rabbitmq::

  wget https://www.rabbitmq.com/releases/rabbitmq-server/v3.6.1/rabbitmq-server-3.6.1-1.noarch.rpm
  rpm --import https://www.rabbitmq.com/rabbitmq-signing-key-public.asc
  yum install rabbitmq-server-3.6.1-1.noarch.rpm

Start Service::

  systemctl start rabbitmq-server.service
  systemctl enable rabbitmq-server.service

.. _RabbitMQ: https://www.rabbitmq.com/
.. _EPEL repos: https://fedoraproject.org/wiki/EPEL/FAQ#howtouse
