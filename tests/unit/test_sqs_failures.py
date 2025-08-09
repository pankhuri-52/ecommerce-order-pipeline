import pytest
from botocore.exceptions import EndpointConnectionError
import worker.worker as worker_module
import logging

def test_sqs_connection_failure(monkeypatch, caplog):
    """Test that SQS connection failures are handled gracefully"""
    
    caplog.set_level(logging.ERROR)
    
    def mock_get_queue_url(**kwargs):
        raise EndpointConnectionError(endpoint_url="http://fake-sqs")

    # Mock the SQS client to raise an error when getting queue URL
    sqs_client = worker_module.get_sqs_client()
    monkeypatch.setattr(sqs_client, "get_queue_url", mock_get_queue_url)

    # Test that the get_queue_url function raises the expected error
    with pytest.raises(EndpointConnectionError):
        worker_module.get_queue_url(sqs_client)
