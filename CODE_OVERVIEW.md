# Code Overview

This document explains how the scraper is organized, how control flows between scripts, and how to work with logs while debugging.

## High-Level Flow

1. `main.py` (orchestrator) optionally refreshes module links.
2. `main.py` loads links from `module_links.txt`.
3. `main.py` launches `one-module.py` for each link.
4. `one-module.py` logs in and calls `start_quiz` from `reader.py`.
5. `reader.py` starts quiz mode, finds answers, and submits each question.

## File-by-File Breakdown

### `main.py`

Purpose:
- Entry point for end-to-end automation.

Responsibilities:
- Parse CLI options (`--workers`, `--skip-collect`).
- Run `link_graber.py` to collect module links unless skipped.
- Read module links with `read_module_links` from `scraper_paths.py`.
- Spawn module workers with `ThreadPoolExecutor`.
- Stream subprocess output to a unified logger.

Important behavior:
- Uses a Python executable resolver so subprocesses prefer the project venv when Selenium is not available in the current interpreter.

### `link_graber.py`

Purpose:
- Log in to S-TEC and build `module_links.txt`.

Responsibilities:
- Open login page and authenticate.
- Navigate to Training -> All Modules.
- Collect module links (`/module/composite/`).
- Skip completed modules during collection.
- Deduplicate links and write to `module_links.txt`.

Completion filtering details:
- Checks each module card/link for completion signals:
  - completion text (`complete`, `completed`, `passed`, `100%`)
  - completion-like class names
  - progress values (`aria-valuenow`, visible progress text)
- Keeps incomplete modules in the saved list.

### `one-module.py`

Purpose:
- Run one module session from either:
  - a numeric index (`--start-module`), or
  - a direct module URL (`--module-link`).

Responsibilities:
- Load one module URL.
- Open browser and log in.
- Delegate quiz automation to `reader.start_quiz`.

Important behavior:
- Supports `--no-prompt` so it can be run non-interactively by `main.py`.
- Uses the same venv bootstrap pattern to avoid missing Selenium errors.

### `reader.py`

Purpose:
- Quiz automation engine.

Responsibilities:
- Open module in a new tab.
- Try to start/skip intro video.
- Move into quiz mode.
- Extract the correct answer from page HTML.
- Click matching answer choices and submit.
- Continue until no more quiz answers are available.

Robustness behavior:
- Uses retries and fallbacks for stale elements and click failures.
- Uses JS click fallbacks where standard Selenium clicks may fail.

### `scraper_paths.py`

Purpose:
- Shared path utilities for `module_links.txt`.

Responsibilities:
- `read_module_links()`
- `write_module_links()`

## Logger Guide

All scripts use Python `logging` with this format:

```text
%(asctime)s %(levelname)s %(message)s
```

Example log line:

```text
2026-04-14 22:47:40,379 INFO Starting worker-1: /home/nsa/code/s-tec-scraper-main/venv/bin/python one-module.py --module-link ...
```

## Ways to Read Logs

### 1. Real-time terminal output

Run scripts directly and watch logs stream:

```bash
python3 main.py -sc -w 1
```

### 2. Save logs to a file while still seeing output

```bash
python3 main.py -sc -w 1 2>&1 | tee run.log
```

### 3. Save logs silently to a file

```bash
python3 main.py -sc -w 1 > run.log 2>&1
```

### 4. Follow a log file live

```bash
tail -f run.log
```

### 5. Filter for warnings/errors only

```bash
grep -E "WARNING|ERROR|Traceback|ModuleNotFoundError" run.log
```

### 6. Filter by worker label

```bash
grep "\[worker-1\]" run.log
```

### 7. Search for one module link across logs

```bash
grep "module/composite/10483283" run.log
```

## Common Log Patterns

- `Starting worker-N`:
  - A new module subprocess started.
- `Opened s-tec module page`:
  - Worker reached module URL successfully.
- `Clicked login button` and `Logged in successfully`:
  - Authentication succeeded.
- `Skipped X completed modules` (collector):
  - Completed modules were excluded from `module_links.txt`.
- `Traceback` / `ERROR`:
  - A hard failure occurred and needs investigation.

## Debugging Tips

- Start with one worker for reproducible logs:

```bash
python3 main.py -sc -w 1 2>&1 | tee debug.log
```

- Increase workers only after single-worker runs are stable.
- If logs are noisy, use `grep` filters shown above.
- If one module keeps failing, run that module directly:

```bash
python3 one-module.py --module-link https://na.s-tec.shimano.com/module/composite/XXXXX
```
