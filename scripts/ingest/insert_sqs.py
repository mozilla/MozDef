import json

import boto3


# AWS SQS Queue URL and access & secret keys
QUEUE = ''
ACCESS_KEY_ID = ''
SECRET_KEY = ''
REGION = 'us-west-2'

# Contents of the message to send to SQS
MESSAGE_BODY = {}


def main():
    session = boto3.session.Session(
        aws_access_key_id=ACCESS_KEY_ID,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION)

    sqs = session.client('sqs')

    response = sqs.send_message(
        QueueUrl=QUEUE,
        MessageBody=json.dumps(MESSAGE_BODY))

    print('Got response with message ID: {}'.format(
        response.get('MessageId')))


if __name__ == '__main__':
    main()
