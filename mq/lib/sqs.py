import boto3
from .aws import get_aws_credentials


def connect_sqs(region_name=None, aws_access_key_id=None,
                aws_secret_access_key=None, task_exchange=None):
    sqs = boto3.resource(
        'sqs',
        **get_aws_credentials(region_name, aws_access_key_id, aws_secret_access_key)
    )
    queue = sqs.get_queue_by_name(QueueName=task_exchange)
    return queue
