import boto3
import json
import time
import redis
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
QUEUE_NAME = os.getenv("QUEUE_NAME", "orders")
LOCALSTACK_URL = os.getenv("LOCALSTACK_URL", "http://localstack:4566")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Logging Setup 
log_filename = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
logging.basicConfig(
    filename=log_filename,
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

# SQS Connection
def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=LOCALSTACK_URL,
        region_name=AWS_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test")
    )

# Redis Connection
def get_redis_client():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_queue_url(sqs_client):
    try:
        response = sqs_client.get_queue_url(QueueName=QUEUE_NAME)
        return response["QueueUrl"]

    except sqs_client.exceptions.QueueDoesNotExist:
        logger.error(f"Queue '{QUEUE_NAME}' does not exist!")
        response = sqs_client.create_queue(QueueName=QUEUE_NAME)
        logger.info(f"Created queue")
        return response["QueueUrl"]

    except Exception as e:
        logger.error(f"Failed to get queue URL: {e}")
        raise

#  Validation
def validate_order(order):
    required_fields = ["order_id", "user_id", "order_value", "items"]

    # Required fields validation
    for field in required_fields:
        if field not in order:
            logger.warning(f"Missing required field: {field} in order {order}")
            return False

    # Data type validation
    if not isinstance(order["order_value"], (int, float)):
        logger.warning(f"Invalid order_value type in order {order}")
        return False

    # Business logic validation
    calculated_value = sum(item["quantity"] * item["price_per_unit"] for item in order["items"])
    if round(calculated_value, 2) != round(order["order_value"], 2):
        logger.warning(f"Order value mismatch in {order['order_id']}: expected {calculated_value}, got {order['order_value']}")
        return False

    return True

# Processing
def process_message(message_body, redis_client):
    try:
        order = json.loads(message_body)
        if not validate_order(order):
            logger.info(f"Skipping invalid order: {order}")
            return

        user_id = order["user_id"]
        order_value = float(order["order_value"])

        # Store in Redis
        redis_client.hincrby(f"user:{user_id}", "order_count", 1)
        redis_client.hincrbyfloat(f"user:{user_id}", "total_spend", order_value)
        redis_client.hincrby("global:stats", "total_orders", 1)
        redis_client.hincrbyfloat("global:stats", "total_revenue", order_value)

        # Update sorted set for spend
        redis_client.zincrby("users:by_spend", order_value, user_id)

        # Update sorted set for order count
        redis_client.zincrby("users:by_count", 1, user_id)

        # Store order by date
        order_date = order["order_timestamp"][:10]  # YYYY-MM-DD
        redis_client.hincrby(f"stats:{order_date}", "orders", 1)
        redis_client.hincrbyfloat(f"stats:{order_date}", "revenue", order_value)


        logger.info(f"Processed order: {order['order_id']} for user {user_id}, value {order_value}")

    except json.JSONDecodeError:
        logger.error(f"Failed to decode message: {message_body}")
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

# Main Worker Loop
def main():
    sqs_client = get_sqs_client()
    redis_client = get_redis_client()
    queue_url = get_queue_url(sqs_client)

    logger.info(f"Worker started, listening to queue: {QUEUE_NAME}")

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
            logger.info("No messages found")

        time.sleep(2)

if __name__ == "__main__":
    main()
