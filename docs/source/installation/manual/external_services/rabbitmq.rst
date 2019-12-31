RabbitMQ
********

`RabbitMQ`_ is used on workers to have queues of events waiting to be inserted into the Elasticsearch cluster (storage).

RabbitMQ does provide a zero-dependency RPM that you can find for RedHat/CentOS here::
https://github.com/rabbitmq/erlang-rpm

For Debian/Ubuntu based distros you would need to install erlang separately.

To install it, first make sure you enabled `EPEL repos`_. Then you need to install an Erlang environment.

If you prefer to install all the dependencies on a Red Hat based system you can do the following::
On Yum-based systems::

  yum install erlang

You can then install the rabbitmq server::

  rpm --import https://www.rabbitmq.com/rabbitmq-signing-key-public.asc
  yum install rabbitmq-server

To start rabbitmq at startup::

  systemctl enable rabbitmq-server

On APT-based systems ::

  sudo apt-get install rabbitmq-server
  sudo invoke-rc.d rabbitmq-server start

We do advise using rabbitmq and erlang's latest versions if you plan on using TLS protected connections with Rabbitmq.
A simple way of doing this would be to use Bintray's repo located at: https://www.rabbitmq.com/install-rpm.html#bintray
to download both the latest versions of rabbitmq and erlang.

.. _RabbitMQ: https://www.rabbitmq.com/
.. _EPEL repos: https://fedoraproject.org/wiki/EPEL/FAQ#howtouse
