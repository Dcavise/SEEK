# tests/unit/test_debug_utils.py
import pytest
import time
import json
from pathlib import Path
import tempfile
import os


def test_timer_decorator():
    """Test the timer decorator functionality"""
    from src.utils.debug import timer
    
    @timer
    def test_function():
        time.sleep(0.01)  # Small delay for timing
        return "success"
    
    result = test_function()
    assert result == "success"


def test_timer_decorator_with_exception():
    """Test timer decorator handles exceptions properly"""
    from src.utils.debug import timer
    
    @timer
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError, match="Test error"):
        failing_function()


def test_debug_dump():
    """Test debug data dumping functionality"""
    from src.utils.debug import debug_dump
    
    # Test data
    test_data = {
        'operation': 'test',
        'count': 42,
        'items': ['a', 'b', 'c']
    }
    
    # Save to debug output
    debug_dump(test_data, "test_dump")
    
    # Check that file was created
    debug_dir = Path("debug_output")
    assert debug_dir.exists()
    
    # Find the created file (will have timestamp)
    json_files = list(debug_dir.glob("test_dump_*.json"))
    assert len(json_files) > 0
    
    # Verify file contents
    with open(json_files[-1]) as f:
        loaded_data = json.load(f)
    
    assert loaded_data == test_data


def test_debug_context_success():
    """Test DebugContext for successful operations"""
    from src.utils.debug import DebugContext
    
    with DebugContext("test_operation") as ctx:
        time.sleep(0.01)
        result = "completed"
    
    # Should complete without error
    assert result == "completed"


def test_debug_context_with_exception():
    """Test DebugContext handles exceptions and creates debug files"""
    from src.utils.debug import DebugContext
    
    with pytest.raises(ValueError):
        with DebugContext("failing_operation"):
            raise ValueError("Test failure")
    
    # Check that error debug file was created
    debug_dir = Path("debug_output")
    error_files = list(debug_dir.glob("error_failing_operation_*.json"))
    assert len(error_files) > 0
    
    # Verify error file contents
    with open(error_files[-1]) as f:
        error_data = json.load(f)
    
    assert error_data['operation'] == 'failing_operation'
    assert 'Test failure' in error_data['error']
    assert 'traceback' in error_data


def test_import_parcels_example():
    """Test the example import_parcels function"""
    from src.utils.debug import import_parcels
    
    result = import_parcels("test_file.csv")
    assert result == "Processed test_file.csv"


def teardown_function():
    """Clean up debug files after tests"""
    debug_dir = Path("debug_output")
    if debug_dir.exists():
        for file in debug_dir.glob("*.json"):
            file.unlink()
        # Try to remove directory if empty
        try:
            debug_dir.rmdir()
        except OSError:
            pass  # Directory not empty or doesn't exist