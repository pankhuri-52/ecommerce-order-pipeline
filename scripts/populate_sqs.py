import boto3
import json
import random
from datetime import datetime, timedelta, timezone

QUEUE_NAME = "orders"
LOCALSTACK_URL = "http://localhost:4566"

# Connect to SQS
sqs_client = boto3.client(
    "sqs",
    endpoint_url=LOCALSTACK_URL,
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# Get or create queue URL - create queue if it doesn't exist
def get_or_create_queue(sqs_client, queue_name):
    try:
        # Try to get existing queue
        response = sqs_client.get_queue_url(QueueName=queue_name)
        queue_url = response["QueueUrl"]
        print(f"Using existing queue: {queue_name}")
        return queue_url

    except sqs_client.exceptions.QueueDoesNotExist:
        # Create queue if it doesn't exist
        print(f"Queue '{queue_name}' not found. Creating...")
        response = sqs_client.create_queue(QueueName=queue_name)
        queue_url = response["QueueUrl"]
        print(f"Created queue: {queue_url}")
        return queue_url

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

queue_url = get_or_create_queue(sqs_client, QUEUE_NAME)

# Generate random order
def generate_order(order_id, user_id):
    items = [
        {
            "product_id": f"P{str(random.randint(1, 999)).zfill(3)}",
            "quantity": random.randint(1, 3),
            "price_per_unit": round(random.uniform(10, 100), 2)
        }
        for _ in range(random.randint(1, 3))
    ]
    order_value = round(sum(item["quantity"] * item["price_per_unit"] for item in items), 2)
    order_timestamp = (datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))).isoformat().replace('+00:00', 'Z')

    return {
        "order_id": f"ORD{order_id}",
        "user_id": f"U{user_id}",
        "order_timestamp": order_timestamp,
        "order_value": order_value,
        "items": items,
        "shipping_address": "123 Main St, Springfield",
        "payment_method": random.choice(["CreditCard", "DebitCard", "PayPal"])
    }

# Send N random orders
def send_orders(count):
    for i in range(count):
        order = generate_order(order_id=1000+i, user_id=random.randint(100, 105))
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(order)
        )
        print(f"Sent order: {order['order_id']} for user {order['user_id']}")

if __name__ == "__main__":
    send_orders(10)  # Change number to send more orders
