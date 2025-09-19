#!/usr/bin/env python3
"""
A Python companion to the original `mkvnmp4` shell script.
Provides similar commands:
  --send    : enqueue MKV/M4V files to Subler
  --wait    : enqueue and wait for Subler to finish and then delete originals
  --rm      : remove duplicate mkv/m4v files that have corresponding mp4
  --dup     : list duplicates
Flags:
  --dry-run : print actions without modifying files or calling Subler
  --yes     : assume yes for prompts
  -v/--verbose : increase verbosity

Config file locations (checked in order):
  /etc/mkvnmp4.conf
  /etc/mkvnmp4/mkvnmp4.conf
  ~/.mkvnmp4.conf
  ~/.config/mkvnmp4.conf

Config file format: plain text file with directories, one per line. Lines starting with # are ignored.
"""

from __future__ import annotations
import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Iterable


def run_applescript(script: str) -> bool:
    """Run AppleScript using PyObjC (NSAppleScript) when available, else fall back to osascript.
    Returns True on success, False on failure."""
    try:
        # Try PyObjC first (macOS)
        from Foundation import NSAppleScript

        sc = NSAppleScript.alloc().initWithSource_(script)
        result, error = sc.executeAndReturnError_(None)
        if error is not None and len(error) > 0:
            # error is an NSDictionary-like object
            try:
                err_msg = str(error)
            except Exception:
                err_msg = "Unknown AppleScript error"
            print(f"AppleScript error: {err_msg}", file=sys.stderr)
            return False
        return True
    except Exception:
        # Fallback to osascript subprocess
        try:
            subprocess.run(["osascript", "-e", script], check=False)
            return True
        except Exception as e:
            print(f"Failed to run osascript: {e}", file=sys.stderr)
            return False


def try_open_with_appkit(files: List[Path], verbose: int = 0) -> bool:
    """Try to open files in Subler using AppKit (NSWorkspace) when PyObjC is installed.
    Returns True on success, False otherwise."""
    try:
        from AppKit import NSWorkspace
        ws = NSWorkspace.sharedWorkspace()
        # prefer application name "Subler"; fullPathForApplication_ returns path if installed
        app_path = ws.fullPathForApplication_("Subler")
        app_arg = "Subler"
        if app_path:
            # pass the app name or path; openFile_withApplication_ accepts application name
            app_arg = "Subler"
        for f in files:
            if verbose:
                print(f"AppKit: opening {f} with Subler")
            ws.openFile_withApplication_(str(f), app_arg)
        return True
    except Exception:
        return False

PROGRAM_NAME = "mkvnmp4.py"
DEFAULT_WAIT = 600

CONFIG_PATHS = [
    Path('/etc/mkvnmp4.conf'),
    Path('/etc/mkvnmp4/mkvnmp4.conf'),
    Path.home() / '.mkvnmp4.conf',
    Path.home() / '.config' / 'mkvnmp4.conf',
]


def read_config() -> List[Path]:
    for p in CONFIG_PATHS:
        if p.exists():
            dirs: List[Path] = []
            for line in p.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                dirs.append(Path(os.path.expanduser(line)))
            return dirs
    raise SystemExit(f"No config file found; looked at: {', '.join(str(p) for p in CONFIG_PATHS)}")


def find_candidates(root: Path, maxdepth: int = 4) -> Iterable[Path]:
    # Walk up to maxdepth — efficient approach is to walk but stop when depth exceeded
    root = root.resolve()
    base_depth = len(root.parts)
    for dirpath, _, filenames in os.walk(root):
        cur_depth = len(Path(dirpath).resolve().parts) - base_depth
        if cur_depth > maxdepth:
            continue
        for name in filenames:
            low = name.lower()
            if low.endswith('.mkv') or low.endswith('.m4v'):
                yield Path(dirpath) / name


def has_mp4_equivalent(path: Path) -> bool:
    if path.suffix.lower() == '.mkv' or path.suffix.lower() == '.m4v':
        mp4 = path.with_suffix('.mp4')
        return mp4.exists()
    return False


def enqueue_to_subler(files: List[Path], dry_run: bool, verbose: int) -> None:
    # Conservative: call osascript per file (keeps parity with shell version)
    if not files:
        return
    if dry_run:
        for f in files:
            print(f"DRY-RUN: would enqueue {f}")
        return

    # Try AppKit-based open (faster, uses system API) when available
    if try_open_with_appkit(files, verbose=verbose):
        return

    # Fallback: applescript per-file
    for f in files:
        # Use raw POSIX path and escape double-quotes for AppleScript
        posix = str(f)
        posix_escaped = posix.replace('"', '\\"')
        as_cmd = f'set filePath to (POSIX file "{posix_escaped}" as alias)\n'
        as_cmd += 'tell application "Subler"\n add to queue filePath\n start queue\n end tell'
        if verbose:
            print(f"Running applescript for: {f}")
        run_applescript(as_cmd)


def enqueue_and_wait(files: List[Path], timeout: int, dry_run: bool, verbose: int) -> None:
    for f in files:
        if dry_run:
            print(f"DRY-RUN: would enqueue and wait for {f} (timeout {timeout}s)")
            continue
        posix = str(f)
        posix_escaped = posix.replace('"', '\\"')
        as_cmd = f'set filePath to (POSIX file "{posix_escaped}" as alias)\n'
        # timeout should be numeric in AppleScript
        as_cmd += f'with timeout of {int(timeout)} seconds\n'
        as_cmd += 'tell application "Subler"\n add to queue filePath\n start queue and wait\n end tell\n'
        as_cmd += 'tell application "Finder"\n if exists file filePath then\n delete file filePath\n end if\n end tell\nend timeout'
        if verbose:
            print(f"Running applescript (wait) for: {f}")
        run_applescript(as_cmd)


def confirm_and_delete(files: List[Path], dry_run: bool, assume_yes: bool) -> None:
    if not files:
        print("No files to delete.")
        return
    print("Files queued for deletion:")
    for f in files:
        print(f"  {f}")
    if dry_run:
        print(f"DRY-RUN: would delete {len(files)} files")
        return
    if not assume_yes:
        ans = input('Proceed with deletion? [y/N]: ').strip().lower()
        if ans not in ('y', 'yes'):
            print('Canceling.')
            return
    # Use AppleScript Finder delete to send to Trash on macOS (consistent with shell script)
    for f in files:
        posix = str(f)
        posix_escaped = posix.replace('"', '\\"')
        as_cmd = f'set filePath to (POSIX file "{posix_escaped}" as alias)\n'
        as_cmd += 'tell application "Finder"\n if exists file filePath then\n delete file filePath\n end if\n end tell'
        run_applescript(as_cmd)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PROGRAM_NAME)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--send', '-s', action='store_true', help='Send to Subler')
    group.add_argument('--wait', '-w', action='store_true', help='Send and wait then delete')
    group.add_argument('--rm', action='store_true', help='Remove duplicate mkv/m4v which have mp4')
    group.add_argument('--dup', action='store_true', help='Show duplicates')
    parser.add_argument('-n', '--dry-run', action='store_true')
    parser.add_argument('-y', '--yes', action='store_true')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('--maxdepth', type=int, default=4)
    parser.add_argument('--wait-timeout', type=int, default=DEFAULT_WAIT)
    args = parser.parse_args(argv)

    try:
        drives = read_config()
    except SystemExit as e:
        print(e)
        return 1

    # Validate drives exist
    existing = [d for d in drives if d.exists()]
    if not existing:
        print('No configured drives are present. Mount them and retry.')
        return 2

    # Find duplicate candidate files across drives
    duplicates: List[Path] = []
    for d in existing:
        for p in find_candidates(d, maxdepth=args.maxdepth):
            if has_mp4_equivalent(p):
                duplicates.append(p)

    if args.dup:
        for p in duplicates:
            print(p)
        return 0

    if args.rm:
        confirm_and_delete(duplicates, dry_run=args.dry_run, assume_yes=args.yes)
        return 0

    if args.send:
        # enqueue files which do not have mp4 equivalent
        to_send: List[Path] = []
        for d in existing:
            for p in find_candidates(d, maxdepth=args.maxdepth):
                if not has_mp4_equivalent(p):
                    to_send.append(p)
        enqueue_to_subler(to_send, dry_run=args.dry_run, verbose=args.verbose)
        return 0

    if args.wait:
        to_send = []
        for d in existing:
            for p in find_candidates(d, maxdepth=args.maxdepth):
                if not has_mp4_equivalent(p):
                    to_send.append(p)
        enqueue_and_wait(to_send, timeout=args.wait_timeout, dry_run=args.dry_run, verbose=args.verbose)
        return 0

    # Default: same behavior as --send
    to_send = []
    for d in existing:
        for p in find_candidates(d, maxdepth=args.maxdepth):
            if not has_mp4_equivalent(p):
                to_send.append(p)
    enqueue_to_subler(to_send, dry_run=args.dry_run, verbose=args.verbose)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
