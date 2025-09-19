import tempfile
import os
from pathlib import Path
import subprocess
import sys

from mkvnmp4 import read_config, find_candidates, has_mp4_equivalent


def test_find_candidates_and_duplicates(tmp_path):
    # create a mock drive directory
    d = tmp_path / "drive"
    d.mkdir()
    (d / "movie.mkv").write_text("dummy")
    (d / "movie.mp4").write_text("dummy mp4")
    # find candidates
    candidates = list(find_candidates(d, maxdepth=1))
    assert any(p.name == "movie.mkv" for p in candidates)
    # check duplicate detection
    assert has_mp4_equivalent(d / "movie.mkv")


def test_read_config(tmp_path, monkeypatch):
    # write a temp config file and ensure read_config picks it up by modifying CONFIG_PATHS
    cfg = tmp_path / "mkvnmp4.conf"
    cfg.write_text(str(tmp_path / "drive") + "\n")
    monkeypatch.setenv('HOME', str(tmp_path))
    # create expected path
    (tmp_path / "drive").mkdir()
    from mkvnmp4 import CONFIG_PATHS
    # temporarily replace CONFIG_PATHS
    old = CONFIG_PATHS.copy()
    try:
        import mkvnmp4 as mod
        mod.CONFIG_PATHS = [cfg]
        dirs = mod.read_config()
        assert dirs[0] == Path(str(tmp_path / "drive"))
    finally:
        mod.CONFIG_PATHS = old
