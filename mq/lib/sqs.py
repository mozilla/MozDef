import boto3


def connect_sqs(region_name=None, aws_access_key_id=None,
                aws_secret_access_key=None, task_exchange=None):
    credentials = {}
    if aws_access_key_id is not None:
        credentials['aws_access_key_id'] = aws_access_key_id
    if aws_secret_access_key is not None:
        credentials['aws_secret_access_key'] = aws_secret_access_key

    sqs = boto3.resource(
        'sqs',
        region_name=region_name,
        **credentials
    )
    queue = sqs.get_queue_by_name(QueueName=task_exchange)
    return queue
