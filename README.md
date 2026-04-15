# S-TEC Scraper

Automates the S-TEC training flow in Selenium, collects module URLs from the All Modules page, and can launch quizzes for saved modules.

## Setup

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Create a `.env` file with these values:
   - `user`
   - `password`

## Usage

### Collect module links

Run:

```bash
python link_graber.py
```

This logs into S-TEC, opens the All Modules page, filters the page down to real module links, deduplicates them, and writes the result to `module_links.txt` next to the scripts.

### Start a single module

Run:

```bash
python one-module.py --start-module 1
```

Options:

- `--start-module`: 1-based index into `module_links.txt`
- `--module-link` or `-ml`: direct module URL, which overrides `--start-module`

### Run the full flow

Run:

```bash
python main.py
```

This script first runs `link_graber.py` to refresh `module_links.txt`, then launches `one-module.py` for each saved module link.

You can parallelize the module runs with:

```bash
python main.py --workers 4
```

Use `--skip-collect` if you already have a fresh `module_links.txt` and want to skip the collection step.

## Notes

- The module list path is shared across scripts so reading and writing stays consistent.
- Logging is enabled with timestamps so you can trace login, navigation, filtering, and save steps.
- The worker count controls how many module-runner subprocesses are active at once.

## Developer Docs

- See `CODE_OVERVIEW.md` for architecture notes, file-by-file responsibilities, and a logger guide with log-reading commands.
