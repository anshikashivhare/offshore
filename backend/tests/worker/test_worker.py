import pytest
from unittest.mock import MagicMock
from app.worker.tasks import process_generic_job

def test_process_generic_job_routing():
    # We test the core logic without full celery harness by mocking self
    mock_self = MagicMock()
    mock_self.retry = Exception("retry_called")
    
    # Test dataset ingestion routing
    try:
        process_generic_job.update_state = mock_self.update_state
        res = process_generic_job("123", "dataset_ingestion", {"key": "value"})
        assert res["status"] == "completed"
        # update_state should be called with RUNNING multiple times
        mock_self.update_state.assert_called()
    except Exception as e:
        # Since we use time.sleep, it shouldn't fail unless there's a bug
        pytest.fail(f"Task raised exception: {e}")

def test_process_generic_job_failure():
    mock_self = MagicMock()
    
    class MockRetry(Exception):
        def __init__(self, *args, **kwargs):
            pass
        
    mock_self.retry = MockRetry
    mock_self.update_state.side_effect = ValueError("Something broke")
    
    with pytest.raises(MockRetry):
        process_generic_job.update_state = mock_self.update_state
        process_generic_job.retry = MockRetry
        process_generic_job("123", "unknown", {})
