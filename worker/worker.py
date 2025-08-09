import boto3
import json
import time

QUEUE_NAME = "orders"
LOCALSTACK_URL = "http://localstack:4566"  # Docker network hostname for Localstack

def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=LOCALSTACK_URL,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

def get_queue_url(sqs_client):
    response = sqs_client.get_queue_url(QueueName=QUEUE_NAME)
    return response["QueueUrl"]

def process_message(message_body):
    try:
        order = json.loads(message_body)
        print(f"Received order: {order}")
    except json.JSONDecodeError:
        print(f"Failed to decode message: {message_body}")

def main():
    sqs_client = get_sqs_client()
    queue_url = get_queue_url(sqs_client)
    print(f"📥 Listening to queue: {QUEUE_NAME}")

    while True:
        messages = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5
        )

        if "Messages" in messages:
            for msg in messages["Messages"]:
                process_message(msg["Body"])

                # Delete after processing
                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
        else:
            print("No messages, waiting...")

        time.sleep(2)

if __name__ == "__main__":
    main()
 