from boto import sqs
import boto
import boto.utils


def connect_sqs(region=None, aws_access_key_id=None,
                aws_secret_access_key=None, task_exchange=None):
    if region is None:
        try:
            # connect_sqs defaults to us-east-1 instead of the local region
            region = boto.utils.get_instance_identity(
                timeout=0.5, num_retries=1)['document']['region']
        except IndexError:
            raise Exception(
                "Unable to determine AWS region. Region isn't configured and "
                "MozDef isn't running in AWS")

    credentials = {}
    if aws_access_key_id is not None:
        credentials['aws_access_key_id'] = aws_access_key_id
    if aws_secret_access_key is not None:
        credentials['aws_secret_access_key'] = aws_secret_access_key
    conn = sqs.connect_to_region(
        region_name=region,
        **credentials
    )

    queue = conn.get_queue(task_exchange)
    return conn, queue
