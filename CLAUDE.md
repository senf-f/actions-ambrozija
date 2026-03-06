# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pollen data scraper for Croatian cities. Scrapes daily pollen concentration data from stampar.hr/hr/peludna-prognoza using Selenium, stores results in CSV files and SQLite, and sends Telegram alerts when new plant species appear.

## Architecture

There are two scraper implementations:

- **Old scraper** (`main.py` at root): Monolithic script using Selenium + CSV output. Runs via `scraping_run_old.yml` (daily at 9:30 UTC) and `run_manually_old.yml`.
- **New scraper** (`src/main.py`): Refactored version with separated concerns. Runs via `scraping_run.yml` (daily at 10:30 UTC) and `run_scraper_manually.yml` / `manual_run.yml`.

New scraper modules in `src/`:
- `scraper.py` — Selenium driver setup and pollen data extraction
- `db_handler.py` — SQLite setup and insert (DB stored at `db/pollen_data.db`)
- `config.py` — Paths, URLs, and constants
- `biljke.py` — Plant species enum (`Biljka`) with reverse lookup dict

Supporting files:
- `biljke.py` (root) — Same enum without the reverse lookup, used by old scraper
- `telegram_sender.py` — Sends messages via Telegram Bot API using env vars
- `app/` — Flask web app (`run.py` to start) for browsing pollen data from SQLite

## Running

```bash
# New scraper
python src/main.py

# Old scraper
python main.py

# Flask web app
python run.py
```

Python 3.9. Dependencies in `requirements.txt`. Requires Chrome/Chromium for Selenium (runs headless).

## Environment Variables

- `TELEGRAM_API_TOKEN_STAMPAR` — Telegram bot token
- `TELEGRAM_CHAT_ID` — Telegram chat ID
- `BASE_DIR` — Set by GitHub Actions to `${{ github.workspace }}`
- `PYTHONPATH=.` — Required when running `src/main.py` from repo root

## Data Storage

- CSV files: `data/{year}/{month}/` — one file per city-plant-month combination
- SQLite: `db/pollen_data.db` — single `pollen_data` table with unique constraint on `(city, plant, date)`

## GitHub Actions

All workflows use the `prod` environment and auto-commit data back to `main`. Secrets (`TELEGRAM_CHAT_ID`, `TELEGRAM_API_TOKEN_STAMPAR`) are configured in the `prod` environment.
