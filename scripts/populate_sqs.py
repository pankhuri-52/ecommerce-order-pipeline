import boto3
import json
import random
from datetime import datetime, timedelta

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

# Get queue URL
queue_url = sqs_client.get_queue_url(QueueName=QUEUE_NAME)["QueueUrl"]

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
    order_timestamp = (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat() + "Z"

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
def send_orders(count=10):
    for i in range(count):
        order = generate_order(order_id=1000+i, user_id=random.randint(100, 105))
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(order)
        )
        print(f"Sent order: {order['order_id']} for user {order['user_id']}")

if __name__ == "__main__":
    send_orders(20)  # Change number to send more orders
