#!/usr/bin/env python
import sys
import pika
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel=connection.channel()
channel.queue_delete(queue=sys.argv[1])
connection.close()
