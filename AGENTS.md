# Agent Context

## Purpose
- This repo hosts a static web-based 2AFC study UI intended for GitHub Pages.
- The app loads trial definitions from `experiment/trial.csv`, renders two filtered variants of the same image, records participant choices and timing, and submits a JSON payload to a configurable backend endpoint.
- There is no server implementation in this repo. Treat backend integration as an HTTP contract only.

## Current App Shape
- `index.html`: single-page shell with three UI states: intro, active trial, finish/submission.
- `assets/js/config.js`: runtime configuration surface for study title, instructions, CSV URL, submit URL, and debug logging.
- `assets/js/app.js`: app state, CSV loading/parsing, trial randomization, response logging, submission, and JSON export.
- `assets/styles/app.css`: polished responsive styling for the study flow.
- `vendor/instagram.min.css`: local filter-class shim used by the current trial definitions.
- `experiment/trial.csv`: source-of-truth trial table. Expected columns are `trial_id`, `img`, `img_path`, `filter_1`, `filter_2`.

## Data Flow
1. App bootstraps from `index.html` and reads `window.STUDY_CONFIG`.
2. It fetches `experiment/trial.csv` over HTTP and parses rows client-side.
3. For each trial, the app randomizes whether `filter_1` or `filter_2` appears on the left.
4. It records one response object per trial with trial metadata, presented mapping, selected side/filter, and timing.
5. On completion, it builds a payload with top-level session metadata plus the per-trial response array.
6. If `submitUrl` is configured, it submits the payload with `POST` and `Content-Type: application/json`.
7. If submission fails, the participant can retry or download a JSON backup from the browser.

## Important Implementation Constraints
- The site is designed for static hosting. Do not introduce server-only assumptions into the core flow.
- Client-side CSV loading requires HTTP hosting. Opening `index.html` directly via `file://` will not satisfy the fetch-based flow.
- Keep trial presentation deterministic per render except for the left/right randomization.
- Preserve the response payload fields already emitted by `assets/js/app.js` unless there is a deliberate contract change.
- The current filter stylesheet is a local compatibility shim, not a complete upstream Instagram filter library.

## Context Engineering Notes
- Read `assets/js/app.js` first when changing study behavior, state transitions, payload shape, or trial sequencing.
- Read `index.html` and `assets/styles/app.css` together when changing layout, accessibility affordances, or responsive behavior.
- Read `assets/js/config.js` before adding hard-coded study copy or endpoint values.
- Treat `experiment/trial.csv` as researcher-managed content. Validation should be strict enough to surface malformed rows clearly.
- If new filters are introduced in the CSV, update `vendor/instagram.min.css` or replace it with the intended filter library before assuming those classes exist.

## Safe Extension Points
- Add optional keyboard shortcuts without changing the click/tap flow.
- Add preloading for upcoming images to reduce inter-trial latency.
- Add richer submission diagnostics as long as the retry/export recovery path remains intact.
- Add new study metadata fields to the top-level payload if they are clearly backward-compatible.

## Verification Expectations
- At minimum, syntax-check JavaScript with `node --check assets/js/app.js`.
- Prefer serving the repo over local HTTP for manual testing because CSV fetches require it.
- When changing payload or submission behavior, verify both success and failure states.
