# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Pollen data scraper for Croatian cities. Scrapes daily pollen concentration data from stampar.hr/hr/peludna-prognoza using Selenium, stores results in CSV files and SQLite, and sends a Telegram alert when a species outside the `Biljka` enum shows up.

## Architecture

The scraper (`src/main.py`) runs via `scraping_run.yml` (daily at 10:30 UTC, also manually dispatchable).

Modules in `src/`:
- `scraper.py` — Selenium driver setup and pollen data extraction
- `db_handler.py` — SQLite setup and insert (DB stored at `db/pollen_data.db`)
- `config.py` — Paths, URLs, and constants
- `biljke.py` — Plant species enum (`Biljka`) with reverse lookup dict
- `telegram.py` — Sends alerts via Telegram Bot API; a no-op when the env vars are unset

Supporting files:
- `app/` — Flask web app (`run.py` to start) for browsing pollen data from SQLite

## Running

```bash
# Scraper
python src/main.py

# Flask web app
python run.py
```

Python 3.13. Dependencies in `requirements.txt`. Requires Chrome/Chromium for Selenium (runs headless).

## Environment Variables

- `TELEGRAM_API_TOKEN_STAMPAR` — Telegram bot token (alerts are skipped if unset)
- `TELEGRAM_CHAT_ID` — Telegram chat ID
- `BASE_DIR` — Set by GitHub Actions to `${{ github.workspace }}`
- `PYTHONPATH=.` — Required when running `src/main.py` from repo root

## Data Storage

- CSV files: `data/{year}/{month}/` — one file per city-plant-month combination
- SQLite: `db/pollen_data.db` — single `pollen_data` table with unique constraint on `(city, plant, date)`

## GitHub Actions

All workflows use the `prod` environment and auto-commit data back to `main`.
