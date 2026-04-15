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

This script collects module links and then starts quiz automation for every fourth module link, which matches the page layout where only every fourth link points to a module.

## Notes

- The module list path is shared across scripts so reading and writing stays consistent.
- Logging is enabled with timestamps so you can trace login, navigation, filtering, and save steps.
