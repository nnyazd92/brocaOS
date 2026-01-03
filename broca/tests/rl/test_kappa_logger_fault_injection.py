from __future__ import annotations

from pathlib import Path

from broca.rl.kappa_logger import KappaSeriesLogger


def test_kappa_logger_writes_csv(tmp_path: Path):
    p = tmp_path / "kappa.csv"
    lg = KappaSeriesLogger(enabled=True, log_file=str(p), append=True)
    lg.log_kappa(0.5)
    assert p.exists()
    txt = p.read_text(encoding="utf-8")
    assert "timestamp,kappa" in txt


