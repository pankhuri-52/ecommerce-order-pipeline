import pytest
from worker.worker import validate_order

def test_valid_order():
    order = {
        "order_id": "ORD1",
        "user_id": "U1",
        "order_value": 50.0,
        "items": [
            {"product_id": "P001", "quantity": 2, "price_per_unit": 25.0}
        ]
    }
    assert validate_order(order) is True

def test_missing_field():
    order = {
        "user_id": "U1",
        "order_value": 50.0,
        "items": [
            {"product_id": "P001", "quantity": 2, "price_per_unit": 25.0}
        ]
    }
    assert validate_order(order) is False

def test_invalid_order_value():
    order = {
        "order_id": "ORD1",
        "user_id": "U1",
        "order_value": 99.0,  # Wrong sum
        "items": [
            {"product_id": "P001", "quantity": 2, "price_per_unit": 25.0}
        ]
    }
    assert validate_order(order) is False
