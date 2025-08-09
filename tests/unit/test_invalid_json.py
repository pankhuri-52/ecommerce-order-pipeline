import pytest
import worker.worker as worker_module
import logging

def test_invalid_json_message(caplog):
    """Test that invalid JSON messages are handled gracefully"""
    
    # Set logging level to capture warnings
    caplog.set_level(logging.ERROR)
    
    # Create a mock Redis client
    class MockRedis:
        def hincrby(self, *args): pass
        def hincrbyfloat(self, *args): pass
        def zincrby(self, *args): pass
    
    mock_redis = MockRedis()
    
    # Test the process_message function directly with invalid JSON
    worker_module.process_message("{invalid json", mock_redis)
    
    # Check that error was logged
    assert any("Failed to decode message" in record.message for record in caplog.records)
