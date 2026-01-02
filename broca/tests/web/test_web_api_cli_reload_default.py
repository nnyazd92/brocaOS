from __future__ import annotations


def test_web_api_cli_reload_defaults_to_false():
    from broca.web_api import _parse_web_api_args

    args = _parse_web_api_args([])
    assert bool(args.reload) is False


def test_web_api_cli_reload_flag_sets_true():
    from broca.web_api import _parse_web_api_args

    args = _parse_web_api_args(["--reload"])
    assert bool(args.reload) is True

