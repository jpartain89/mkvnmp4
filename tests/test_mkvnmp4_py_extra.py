import builtins
from pathlib import Path
import mkvnmp4


def test_enqueue_prefers_appkit(monkeypatch, tmp_path):
    called = {"appkit": False, "applescript": False}

    def fake_try_open(files, verbose=0):
        called["appkit"] = True
        return True

    def fake_run_applescript(script: str) -> bool:
        called["applescript"] = True
        return True

    monkeypatch.setattr(mkvnmp4, "try_open_with_appkit", fake_try_open)
    monkeypatch.setattr(mkvnmp4, "run_applescript", fake_run_applescript)

    f = tmp_path / "video.mkv"
    f.write_text("x")

    # Should use appkit and not call applescript
    mkvnmp4.enqueue_to_subler([f], dry_run=False, verbose=1)
    assert called["appkit"] is True
    assert called["applescript"] is False


def test_enqueue_fallsback_to_applescript(monkeypatch, tmp_path):
    called = {"applescript_calls": []}

    def fake_try_open(files, verbose=0):
        return False

    def fake_run_applescript(script: str) -> bool:
        called["applescript_calls"].append(script)
        return True

    monkeypatch.setattr(mkvnmp4, "try_open_with_appkit", fake_try_open)
    monkeypatch.setattr(mkvnmp4, "run_applescript", fake_run_applescript)

    f = tmp_path / "video.mkv"
    f.write_text("x")

    mkvnmp4.enqueue_to_subler([f], dry_run=False, verbose=0)

    assert len(called["applescript_calls"]) == 1
    assert "Subler" in called["applescript_calls"][0]
    assert str(f) in called["applescript_calls"][0]


def test_confirm_and_delete_calls_applescript_per_file(monkeypatch, tmp_path):
    calls = []

    def fake_run_applescript(script: str) -> bool:
        calls.append(script)
        return True

    monkeypatch.setattr(mkvnmp4, "run_applescript", fake_run_applescript)

    f1 = tmp_path / "a.mkv"
    f2 = tmp_path / "b.mkv"
    f1.write_text("x")
    f2.write_text("x")

    mkvnmp4.confirm_and_delete([f1, f2], dry_run=False, assume_yes=True)

    # expect run_applescript called twice (once per file)
    assert len(calls) == 2
    assert str(f1) in calls[0]
    assert str(f2) in calls[1]
