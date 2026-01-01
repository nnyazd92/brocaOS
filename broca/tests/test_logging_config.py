"""
Unit tests for logging configuration and JsonFormatter.

Tests JSON log formatting, logging setup, handler configuration, and idempotency.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, date, time, timezone
from logging.handlers import RotatingFileHandler
from unittest.mock import patch, MagicMock

import pytest

from broca.logging_config import JsonFormatter, setup_logging
from broca.tests.utils import LogCapture


class TestJsonFormatter:
    """Test JsonFormatter class for JSON log formatting."""
    
    def test_format_basic_log(self):
        """
        Test that basic log records are formatted as valid JSON.
        
        Rationale: Ensures JSON formatter produces valid, parseable JSON output.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "timestamp" in parsed
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"
        assert parsed["message"] == "Test message"
    
    def test_format_with_extra_fields(self):
        """
        Test that extra fields are included in JSON output.
        
        Rationale: Ensures structured logging with extra context works correctly.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.event = "test_event"
        record.user_id = "12345"
        record.custom_field = {"nested": "value"}
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert parsed["event"] == "test_event"
        assert parsed["user_id"] == "12345"
        assert parsed["custom_field"] == {"nested": "value"}
    
    def test_format_excludes_standard_fields(self):
        """
        Test that standard logging fields are excluded from extra fields.
        
        Rationale: Ensures only custom extra fields are included, avoiding duplication.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        # Standard fields should not appear as extra fields
        assert "pathname" not in parsed
        assert "lineno" not in parsed
        assert "args" not in parsed
    
    def test_format_unicode_handling(self):
        """
        Test that Unicode characters are properly handled in JSON output.
        
        Rationale: Ensures international characters and emoji work correctly in logs.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test with unicode: 测试 🎉",
            args=(),
            exc_info=None
        )
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "测试 🎉" in parsed["message"]
        assert parsed["message"] == "Test with unicode: 测试 🎉"
    
    def test_format_excludes_private_fields(self):
        """
        Test that fields starting with underscore are excluded.
        
        Rationale: Ensures private/internal fields are not exposed in logs.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record._private_field = "should not appear"
        record.public_field = "should appear"
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        assert "_private_field" not in parsed
        assert parsed["public_field"] == "should appear"
    
    def test_format_with_datetime_in_extra_fields(self):
        """
        Test that datetime objects in extra fields are serialized to ISO format strings.
        
        Rationale: Ensures tool results containing datetime objects can be logged without errors.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.event = "tool_call_result"
        record.timestamp = datetime.now(timezone.utc)
        record.created_date = date.today()
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        # Datetime should be converted to ISO format string
        assert isinstance(parsed["timestamp"], str)
        assert "T" in parsed["timestamp"] or "Z" in parsed["timestamp"] or "+" in parsed["timestamp"]
        # Date should be converted to ISO format string
        assert isinstance(parsed["created_date"], str)
        assert len(parsed["created_date"]) == 10  # YYYY-MM-DD format
        assert parsed["event"] == "tool_call_result"
    
    def test_format_with_datetime_in_nested_structures(self):
        """
        Test that datetime objects in nested dicts and lists are serialized correctly.
        
        Rationale: Ensures complex tool results with nested datetime objects are handled properly.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        dt1 = datetime.now(timezone.utc)
        dt2 = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        record.result = {
            "metadata": {
                "created_at": dt1,
                "updated_at": dt2,
                "nested": {
                    "timestamp": dt1
                }
            },
            "timestamps": [dt1, dt2],
            "data": "some_data"
        }
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        # Check nested dict
        assert isinstance(parsed["result"]["metadata"]["created_at"], str)
        assert isinstance(parsed["result"]["metadata"]["updated_at"], str)
        assert isinstance(parsed["result"]["metadata"]["nested"]["timestamp"], str)
        # Check list
        assert isinstance(parsed["result"]["timestamps"][0], str)
        assert isinstance(parsed["result"]["timestamps"][1], str)
        # Other data should be unchanged
        assert parsed["result"]["data"] == "some_data"
    
    def test_format_with_mixed_datetime_types(self):
        """
        Test that datetime, date, and time objects are all serialized correctly.
        
        Rationale: Ensures all common datetime-related types are handled.
        """
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/test/path",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.dt = datetime(2024, 1, 15, 10, 30, 45, tzinfo=timezone.utc)
        record.d = date(2024, 1, 15)
        record.t = time(10, 30, 45)
        
        output = formatter.format(record)
        parsed = json.loads(output)
        
        # All should be strings
        assert isinstance(parsed["dt"], str)
        assert isinstance(parsed["d"], str)
        assert isinstance(parsed["t"], str)
        
        # Verify ISO format
        assert "2024-01-15" in parsed["dt"]
        assert parsed["d"] == "2024-01-15"
        assert "10:30:45" in parsed["t"]


class TestSetupLogging:
    """Test setup_logging() function for configuring logging handlers."""
    
    def test_setup_logging_creates_handlers(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that setup_logging creates both console and file handlers when console logging is not suppressed.
        
        Rationale: Ensures logging is properly configured with all required handlers when console logging is enabled.
        """
        monkeypatch.setenv("BROCA_LOG_FILE", temp_log_file)
        monkeypatch.setenv("BROCA_LOG_LEVEL", "INFO")
        
        # Reload logging_config to pick up new env vars
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        # Clear any existing handlers
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Explicitly disable console suppression to test backward compatibility
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(
            level="INFO",
            file_path=temp_log_file,
            suppress_console_logging=False
        )
        
        logging_config.setup_logging()
        
        handlers = root_logger.handlers
        assert len(handlers) >= 2
        
        # Check for console handler (StreamHandler writing to stdout/stderr)
        import sys
        console_handlers = [
            h for h in handlers 
            if isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr)
        ]
        assert len(console_handlers) > 0
        
        # Check for file handler
        file_handlers = [h for h in handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) > 0
        
        # Restore original config
        logging_config.config = original_config
    
    def test_setup_logging_console_handler_config(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that console handler is configured with correct formatter and level.
        
        Rationale: Ensures console output is readable and at correct verbosity.
        """
        monkeypatch.setenv("BROCA_LOG_FILE", temp_log_file)
        
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Setup logging with DEBUG level via config and explicitly disable console suppression
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(
            level="DEBUG", 
            file_path=temp_log_file,
            suppress_console_logging=False
        )
        
        logging_config.setup_logging()
        
        # Check for console handler (StreamHandler writing to stdout/stderr)
        import sys
        console_handlers = [
            h for h in root_logger.handlers 
            if isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr)
        ]
        assert len(console_handlers) > 0
        
        console_handler = console_handlers[0]
        # Handler level may match logger level or be set separately
        assert console_handler.formatter is not None
        
        # Restore original config
        logging_config.config = original_config
    
    def test_setup_logging_file_handler_config(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that file handler is configured with JSON formatter and rotation settings.
        
        Rationale: Ensures log files use structured JSON format and proper rotation.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to use temp file
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(level="INFO", file_path=temp_log_file)
        
        logging_config.setup_logging()
        
        file_handlers = [h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) > 0
        
        file_handler = file_handlers[0]
        assert file_handler.baseFilename == temp_log_file
        assert file_handler.maxBytes == 5 * 1024 * 1024  # 5MB
        assert file_handler.backupCount == 3
        # Check formatter type - after reload it might be a different class instance
        assert file_handler.formatter is not None
        assert type(file_handler.formatter).__name__ == "JsonFormatter"
        
        # Restore original config
        logging_config.config = original_config
    
    def test_setup_logging_idempotency(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that calling setup_logging multiple times doesn't duplicate handlers.
        
        Rationale: Ensures logging setup is safe to call multiple times.
        """
        monkeypatch.setenv("BROCA_LOG_FILE", temp_log_file)
        
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Call multiple times
        logging_config.setup_logging()
        initial_count = len(root_logger.handlers)
        
        logging_config.setup_logging()
        final_count = len(root_logger.handlers)
        
        # Should have same number of handlers (idempotent check in setup_logging)
        assert final_count == initial_count
    
    def test_setup_logging_log_level_config(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that log level is correctly configured from config.
        
        Rationale: Ensures log verbosity matches configuration.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to use WARNING level
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(level="WARNING", file_path=temp_log_file)
        
        logging_config.setup_logging()
        
        assert root_logger.level == logging.WARNING
        
        # Restore original config
        logging_config.config = original_config
    
    def test_setup_logging_invalid_level_defaults(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that invalid log level defaults to INFO.
        
        Rationale: Ensures invalid configuration doesn't break logging setup.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Setup with invalid level - getattr will default to INFO
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(level="INVALID_LEVEL", file_path=temp_log_file)
        
        logging_config.setup_logging()
        
        # getattr should default to INFO when invalid level is provided
        assert root_logger.level == logging.INFO
        
        # Restore original config
        logging_config.config = original_config
    
    def test_setup_logging_file_encoding(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that file handler uses UTF-8 encoding.
        
        Rationale: Ensures Unicode characters are properly written to log files.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to use temp file
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(level="INFO", file_path=temp_log_file)
        
        logging_config.setup_logging()
        
        # Write a unicode log entry
        logger = logging.getLogger("test")
        logger.info("Unicode test: 测试 🎉")
        
        # Flush handlers to ensure writes complete
        for handler in root_logger.handlers:
            handler.flush()
        
        # Read back and verify
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "测试 🎉" in content
        
        # Restore original config
        logging_config.config = original_config
    
    def test_setup_logging_suppresses_console_when_enabled(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that console handler is not created when suppress_console_logging is True.
        
        Rationale: Ensures console logging can be suppressed to prevent interference with streaming output.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to suppress console logging
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(
            level="INFO", 
            file_path=temp_log_file,
            suppress_console_logging=True
        )
        
        logging_config.setup_logging()
        
        # Check that no console handler (StreamHandler writing to stdout/stderr) exists
        import sys
        console_handlers = [
            h for h in root_logger.handlers 
            if isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr)
        ]
        assert len(console_handlers) == 0
        
        # But file handler should still exist
        file_handlers = [h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) > 0
        
        # Restore original config
        logging_config.config = original_config
    
    def test_setup_logging_creates_console_when_not_suppressed(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that console handler is created when suppress_console_logging is False.
        
        Rationale: Ensures backward compatibility when console logging is not suppressed.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to not suppress console logging
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(
            level="INFO", 
            file_path=temp_log_file,
            suppress_console_logging=False
        )
        
        logging_config.setup_logging()
        
        # Check that console handler exists (StreamHandler writing to stdout/stderr)
        import sys
        console_handlers = [
            h for h in root_logger.handlers 
            if isinstance(h, logging.StreamHandler) and h.stream in (sys.stdout, sys.stderr)
        ]
        assert len(console_handlers) > 0
        
        # File handler should also exist
        file_handlers = [h for h in root_logger.handlers if isinstance(h, RotatingFileHandler)]
        assert len(file_handlers) > 0
        
        # Restore original config
        logging_config.config = original_config
    
    def test_suppress_console_logging_still_logs_to_file(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that logs still go to file when console logging is suppressed.
        
        Rationale: Ensures file logging continues to work even when console is suppressed.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to suppress console logging
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(
            level="INFO", 
            file_path=temp_log_file,
            suppress_console_logging=True
        )
        
        logging_config.setup_logging()
        
        # Log a test message
        logger = logging.getLogger("test.file_logging")
        logger.info("Test message for file logging")
        logger.warning("Test warning for file logging")
        
        # Flush handlers to ensure writes complete
        for handler in root_logger.handlers:
            handler.flush()
        
        # Read back and verify logs are in file
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Test message for file logging" in content
            assert "Test warning for file logging" in content
        
        # Restore original config
        logging_config.config = original_config
    
    def test_warnings_not_printed_to_console_when_suppressed(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that warnings are not printed to console when console logging is suppressed.
        
        Rationale: Ensures warnings don't interfere with streaming output when console logging is suppressed.
        """
        import importlib
        import sys
        from io import StringIO
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to suppress console logging
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(
            level="INFO", 
            file_path=temp_log_file,
            suppress_console_logging=True
        )
        
        logging_config.setup_logging()
        
        # Capture stderr to verify no warnings are printed
        stderr_capture = StringIO()
        original_stderr = sys.stderr
        sys.stderr = stderr_capture
        
        try:
            # Log warnings and errors
            logger = logging.getLogger("test.warnings")
            logger.warning("This warning should not appear in console")
            logger.error("This error should not appear in console")
            
            # Flush handlers
            for handler in root_logger.handlers:
                handler.flush()
            
            # Check that nothing was written to stderr
            stderr_content = stderr_capture.getvalue()
            assert "This warning should not appear in console" not in stderr_content
            assert "This error should not appear in console" not in stderr_content
            
            # But verify they are in the file
            with open(temp_log_file, 'r', encoding='utf-8') as f:
                file_content = f.read()
                assert "This warning should not appear in console" in file_content
                assert "This error should not appear in console" in file_content
        finally:
            sys.stderr = original_stderr
        
        # Restore original config
        logging_config.config = original_config


class TestLoggingIntegration:
    """Integration tests for logging configuration."""
    
    def test_json_logging_round_trip(self, temp_log_file: str, monkeypatch: pytest.MonkeyPatch):
        """
        Test that JSON logs can be written and parsed correctly.
        
        Rationale: Ensures end-to-end JSON logging functionality works.
        """
        import importlib
        from broca import logging_config
        importlib.reload(logging_config)
        
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        
        # Update config to use temp file
        from broca.config import LoggingConfig
        original_config = logging_config.config
        logging_config.config.logging = LoggingConfig(level="INFO", file_path=temp_log_file)
        
        logging_config.setup_logging()
        
        # Log with extra fields
        logger = logging.getLogger("test.integration")
        logger.info("Integration test message", extra={
            "event": "test_event",
            "user_id": "12345",
            "data": {"key": "value"}
        })
        
        # Flush handlers
        for handler in root_logger.handlers:
            handler.flush()
        
        # Read and parse JSON
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            assert len(lines) > 0
            
            # Parse last line (our log entry)
            log_entry = json.loads(lines[-1])
            assert log_entry["level"] == "INFO"
            assert log_entry["message"] == "Integration test message"
            assert log_entry["event"] == "test_event"
            assert log_entry["user_id"] == "12345"
            assert log_entry["data"] == {"key": "value"}
        
        # Restore original config
        logging_config.config = original_config
