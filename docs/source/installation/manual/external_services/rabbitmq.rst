RabbitMQ
********

`RabbitMQ`_ is used on workers to have queues of events waiting to be inserted into the Elasticsearch cluster (storage).


RabbitMQ requires `EPEL repos`_ so we need to first install that::

  yum -y install epel-release

Download and install Rabbitmq::

  wget https://www.rabbitmq.com/releases/rabbitmq-server/v3.6.1/rabbitmq-server-3.6.1-1.noarch.rpm
  rpm --import https://www.rabbitmq.com/rabbitmq-signing-key-public.asc
  yum install -y rabbitmq-server-3.6.1-1.noarch.rpm


COPY docker/compose/rabbitmq/files/rabbitmq.config /etc/rabbitmq/
COPY docker/compose/rabbitmq/files/enabled_plugins /etc/rabbitmq/

Create rabbitmq configuration file::

  vim /etc/rabbitmq/rabbitmq.config

With the following contents::

  [
    {rabbit,
      [
        {tcp_listeners, [5672]},
        {loopback_users, []}
      ]
    },
    {rabbitmq_management,
      [
        {listener,
          [
            {port, 15672},
            {ip, "127.0.0.1"}
          ]
        }
      ]
    }
  ].

Enable management plugin::

  vim /etc/rabbitmq/enabled_plugins

With the following contents::

  [rabbitmq_management].

Start Service::

  systemctl start rabbitmq-server
  systemctl enable rabbitmq-server

.. _RabbitMQ: https://www.rabbitmq.com/
.. _EPEL repos: https://fedoraproject.org/wiki/EPEL/FAQ#howtouse
