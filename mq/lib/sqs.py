from boto import sqs


def connect_sqs(region, access_key, secret_key, task_exchange):
    conn = sqs.connect_to_region(
        region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )

    queue = conn.get_queue(task_exchange)
    return conn, queue
