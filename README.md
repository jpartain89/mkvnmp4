# mkvnmp4

Script to remove duplicated .mkv files from a media server.

## How to install and run

This repository contains two entrypoints:

- `mkvnmp4` (Bash script) — the original shell script for finding `.mkv`/`.m4v` files and enqueuing to Subler or removing duplicates.
- `mkvnmp4.py` (Python) — a Python companion with the same behaviors and optional PyObjC integration on macOS.

Configuration

Create a configuration file that lists the directories to search (one per line). The scripts look for the first existing config in this order:

1. `/etc/mkvnmp4.conf`
2. `/etc/mkvnmp4/mkvnmp4.conf`
3. `~/.mkvnmp4.conf`
4. `~/.config/mkvnmp4.conf`

Each line should contain a path to a directory. Lines starting with `#` are ignored. Example config:

```
/media/movies
/media/tv
```

Developer setup (one-command)

This repo includes a `Makefile` with convenient targets. On macOS with Homebrew installed, to prepare a development environment run:

```
make deps        # create venv and install Python dev deps from requirements-dev.txt
make brew-tools  # install shell tools: shellcheck, shfmt, bats-core (requires Homebrew)
```

Then activate the venv:

```
source venv/bin/activate
```

Run tests

```
make test
```

Lint and format (optional)

```
make lint     # runs shellcheck on mkvnmp4
make format   # formats mkvnmp4 using shfmt
```

Quick usage (regular users)

1. Ensure the config file is present in one of the locations above and lists the directories to search.
2. Run the shell script directly:

```
./mkvnmp4 --help
./mkvnmp4 --dup        # list duplicates
./mkvnmp4 --send       # enqueue to Subler (dry-run to verify first)
./mkvnmp4 --wait       # enqueue and wait (deletes originals after processing)
```

Safety note

- The scripts include `--dry-run` (or `-n`) so you can verify actions first. Use it before enabling destructive operations.
- Deletion moves files to the macOS Trash via Finder automation (AppleScript). Make sure to back up important files.

