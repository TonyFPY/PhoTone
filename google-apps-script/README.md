# Google Apps Script Setup

## What this does
- `Code.gs` accepts the frontend study payload and writes one Google Sheets row per trial.
- Session-level metadata is repeated on each row so the sheet is easy to filter and analyze.
- The frontend is already configured to post Apps Script-compatible form data using the `payload` field.

## Deploy
1. Create a new Google Sheet for study responses.
2. Open `Extensions` -> `Apps Script`.
3. Replace the default script with `google-apps-script/Code.gs`.
4. Save the project.
5. Click `Deploy` -> `New deployment`.
6. Choose `Web app`.
7. Set `Execute as` to your account.
8. Set access to whoever should be allowed to submit.
9. Copy the `/exec` URL.

## Frontend config
Set these values in `assets/js/config.js`:

```js
submitMode: "google-apps-script",
submitUrl: "YOUR_WEB_APP_EXEC_URL",
googleAppsScript: {
  payloadField: "payload",
  useNoCors: true,
},
```

## Saved columns
- `session_id`
- `started_at`
- `completed_at`
- `stage_order`
- `total_stages`
- `total_trials`
- `recorded_trials`
- `user_agent`
- `page_url`
- `stage_name`
- `stage_index`
- `stage_trial_index`
- `stage_trial_count`
- `trial_id`
- `img_id`
- `img_path`
- `filter_left`
- `filter_right`
- `prompt`
- `selected_side`
- `selected_filter`
- `trial_start_timestamp`
- `response_timestamp`
- `reaction_time_ms`
- `received_at`

## Notes
- `useNoCors: true` is the safest default for a GitHub Pages frontend posting to Apps Script.
- With `no-cors`, the browser cannot read the response body, so the frontend treats a completed request as success unless the network call itself throws.
- If your Apps Script deployment supports readable cross-origin responses in your setup, you can set `useNoCors: false`.
