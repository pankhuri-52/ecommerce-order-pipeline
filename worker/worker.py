import boto3
import json
import time
import redis

QUEUE_NAME = "orders"
LOCALSTACK_URL = "http://localstack:4566"
REDIS_HOST = "redis"  # Docker service name for Redis
REDIS_PORT = 6379

# Connect to SQS
def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=LOCALSTACK_URL,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )

# Connect to Redis
def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_queue_url(sqs_client):
    response = sqs_client.get_queue_url(QueueName=QUEUE_NAME)
    return response["QueueUrl"]

# Process and store in Redis
def process_message(message_body, redis_client):
    try:
        order = json.loads(message_body)

        user_id = order.get("user_id")
        order_value = float(order.get("order_value", 0))

        # Update user stats
        redis_client.hincrby(f"user:{user_id}", "order_count", 1) #hash increment by 1
        redis_client.hincrbyfloat(f"user:{user_id}", "total_spend", order_value)

        # Update global stats
        redis_client.hincrby("global:stats", "total_orders", 1)
        redis_client.hincrbyfloat("global:stats", "total_revenue", order_value)

        print(f"Processed order for user {user_id}, value: {order_value}")

    except json.JSONDecodeError:
        print(f"Failed to decode message: {message_body}")

def main():
    sqs_client = get_sqs_client()
    redis_client = get_redis_client()
    queue_url = get_queue_url(sqs_client)

    print(f"Listening to queue: {QUEUE_NAME}")

    while True:
        messages = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=5
        )

        if "Messages" in messages:
            for msg in messages["Messages"]:
                process_message(msg["Body"], redis_client)

                sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=msg["ReceiptHandle"]
                )
        else:
            print("No messages, waiting...")

        time.sleep(2)

if __name__ == "__main__":
    main()
