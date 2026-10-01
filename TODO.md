# TODO

_Last updated: 2026-10-01_

## Code markers
_None found._

## Issues
- [ ] #7 Unaprijediti UX/UI
- [ ] #4 Napraviti aplikaciju za racunanje st. tottering dana

## Working state / follow-ups
- [ ] Migrate Flask web UI from Render to VPS
  - [ ] Provision VPS + install Python, Chrome/Chromium, git
  - [ ] Set up gunicorn as a systemd service (replaces `gunicorn run:app` from `render.yaml`/`Procfile`)
  - [ ] Configure nginx reverse proxy + TLS (Let's Encrypt)
  - [ ] Set env vars (`TELEGRAM_API_TOKEN_STAMPAR`, `TELEGRAM_CHAT_ID`, `PYTHONPATH=.`)
  - [ ] Decide on SQLite DB location/persistence (currently `db/pollen_data.db`)
  - [ ] Point DNS/subdomain to VPS, verify web UI
  - [ ] Decommission Render service (remove `render.yaml`/`Procfile` if fully off Render)
- [ ] Pula is in `AIR_STATIONS` (`src/config.py`) but has zero `air_temp_data` rows (2026-09-02 → 2026-09-21), while the other 5 stations have ~20 each. Check whether `tx.xml` publishes Pula under a different station name, or drop it from the config.
- [ ] Two enum members for the same oak: `Biljka.HRAST = "Hrast (Quercus ilex)"` and `Biljka.HRAST_CRNIKA = "Hrast crnika (Quercus ilex)"` (`src/biljke.py`). `HRAST` has only 24 rows, one per city, all from the one-off 2024-11-01 run, so it shows up as a plant option with no data. Decide whether to drop it from the enum and delete its rows, or relabel them as `HRAST_CRNIKA`.
- [ ] `ubuntu-latest` switches to Ubuntu 26 on 2026-10-19. After that date, check that the scrape workflows still pass (Chrome/Chromium install, Python 3.13 setup). If something breaks, pin `ubuntu-24.04` in `scrape.yml`.
- [ ] 2026-10-01: pollen was run by hand (run 36855638571) while the scheduled run was late. If the scheduled run also fired, check that 2026-10-01 has one row per city and plant in `db/pollen_data.db` and in the CSVs.

## Bugs
- [ ] Concurrent scrape runs can lose a day: `scrape.yml` does `git push origin main` with no pull/rebase and no `concurrency:` group, while the three crons (05:07, 11:00, 16:05) start 3-5 h late and can overlap. Both commit the binary `db/pollen_data.db`, so the second push is rejected. Air data is unbackfillable.
- [ ] One "-" in `oborina.xml` aborts the whole rain run: `rain_scraper.py:24` uses bare `float()`, while `temp_scraper._float` already handles "-".
- [ ] `/compare`'s `fetchPeriod` turns a 400 into "no data", and a CAMS 502 is handled differently on each chart page. Belongs with the series-shaped server interface below.

## Architecture (from the 2026-09-28 review; A and C done)
- [ ] **B. One series-shaped data interface on the server.** The four `/api/*-data` routes return four shapes that the browser reshapes in 2-3 places each. The date-range SQL is repeated 4 times, and the `date(date)` timestamp fix exists only in the pollen query. `/api/graph-data` has no plant param, and `/api/rain-data` has no route test. Test with pytest on a tmp SQLite.
- [ ] **D. DHMZ feed pipeline and a deeper store.** `rain_scraper.main` and `temp_scraper.main` are copies of each other (setup → fetch → parse → insert → close). `_iso` and `_float` exist only in temp. `db_handler.insert` is shallow: callers still pass the table and every column, and it commits per row. `parse_sea` takes an hour it doesn't return. Temp tests pass `str`, not the bytes `fetch_xml` returns. Keep `dhmz.fetch_xml`, it earns its keep.
- [ ] **E. Station ↔ city identity has no single home.** It's encoded five ways: `AIR_STATIONS` is a dict; `SEA_STATIONS` is a tuple where the station name is the city, and `sea_temp_data` has no city column; rain uses a `split("-")[0]` heuristic; `backfill_rain.SHEETS`; `TREND_CITIES` lives in `main.py`. A single home would make a "every configured station has rows" check possible, which would catch the Pula gap above.
- [ ] **F. (Speculative) Collapse the Selenium scraper into one `scrape()` call.** Callers learn a 4-call ordering, and `accept_cookies` swallows every exception. There's only one adapter, so only worth it alongside other scraper work.
- [ ] Untested JS on `/compare`: the leap-Feb case in `axisKeys`, the month end in `periodQuery`, the mode switch, duplicate-row disabling, and the plant union.
- [ ] `db_handler.setup_db` reads the module-global `DB_PATH`, and `app.routes.DB_PATH` is a second binding. Tests monkeypatch both.

## Done
- [x] Backfill historical rain from `mrse.xlsx` (2022-01 → 2026-08) via `src/backfill_rain.py`. Zagreb-aerodrom (Pleso) + Split-Marjan. Note: DHMZ `oborina.xml` publishes Split-**aerodrom**, not Marjan, so Split history won't extend forward under the same station name.
- [x] Commit uncommitted changes: `.gitignore` (committed in `8904c798`)
- [x] Add `.playwright-mcp/` to `.gitignore`
