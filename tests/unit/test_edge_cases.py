import pytest
from worker.worker import validate_order

def test_empty_order_value():
    order = {"user_id": "u1", "order_id": "o1", "order_value": ""}
    assert not validate_order(order)

def test_negative_quantity():
    order = {
        "user_id": "u1",
        "order_id": "o1",
        "order_value": 10,
        "items": [{"quantity": -2, "price_per_unit": 5}]
    }
    assert not validate_order(order)

def test_zero_price():
    order = {
        "user_id": "u1",
        "order_id": "o1",
        "order_value": 0,
        "items": [{"quantity": 1, "price_per_unit": 0}]
    }
    assert validate_order(order)
