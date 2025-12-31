import importlib
import logging

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck


@pytest.fixture
def isolated_tool_selection_logger(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    logger = logging.getLogger("broca.rl.tool_selection")
    original_handlers = list(logger.handlers)
    original_level = logger.level
    original_propagate = logger.propagate

    try:
        logger.handlers[:] = []
        logger.setLevel(logging.NOTSET)
        logger.propagate = True

        import broca.rl.tool_selection_logging as tsl

        tsl = importlib.reload(tsl)
        yield tsl, logger, tmp_path
    finally:
        for handler in list(logger.handlers):
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass
        logger.handlers[:] = original_handlers
        logger.setLevel(original_level)
        logger.propagate = original_propagate


@settings(
    max_examples=25,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None,
)
@given(st.integers(min_value=1, max_value=20))
def test_tool_selection_logger_is_idempotent(isolated_tool_selection_logger, n_calls):
    tsl, _logger, tmp_path = isolated_tool_selection_logger

    for _ in range(n_calls):
        logger = tsl.get_tool_selection_logger()
        logger.info("TEST_LOG_LINE")

    expected_path = (tmp_path / "data" / "rl" / "tool_selection.log").resolve()
    logger = tsl.get_tool_selection_logger()

    file_handlers = [
        h
        for h in logger.handlers
        if isinstance(h, logging.FileHandler)
        and getattr(h, "baseFilename", None) == str(expected_path)
    ]
    assert len(file_handlers) == 1
    assert expected_path.exists()


def test_web_api_uses_shared_tool_selection_logger(isolated_tool_selection_logger):
    tsl, _logger, tmp_path = isolated_tool_selection_logger

    import broca.web_api as web_api

    web_api = importlib.reload(web_api)
    api_logger = web_api._get_tool_selection_logger()

    assert api_logger is tsl.get_tool_selection_logger()

    api_logger.info("API_TEST_LINE")
    for handler in api_logger.handlers:
        try:
            handler.flush()
        except Exception:
            pass

    expected_path = (tmp_path / "data" / "rl" / "tool_selection.log").resolve()
    assert expected_path.exists()
    assert "API_TEST_LINE" in expected_path.read_text(encoding="utf-8")

