const RESPONSE_HEADERS = [
  "session_id",
  "started_at",
  "completed_at",
  "stage_order",
  "total_stages",
  "total_trials",
  "recorded_trials",
  "user_agent",
  "page_url",
  "stage_name",
  "stage_index",
  "stage_trial_index",
  "stage_trial_count",
  "trial_id",
  "img_id",
  "img_path",
  "filter_left",
  "filter_right",
  "prompt",
  "selected_side",
  "selected_filter",
  "trial_start_timestamp",
  "response_timestamp",
  "reaction_time_ms",
  "received_at",
];

function doPost(e) {
  try {
    const payload = parsePayload_(e);
    validatePayload_(payload);

    const sheet = getOrCreateSheet_();
    ensureHeaders_(sheet);

    const receivedAt = new Date().toISOString();
    const session = payload.session;
    const rows = payload.trials.map((trial) => [
      session.session_id,
      session.started_at,
      session.completed_at,
      Array.isArray(session.stage_order) ? session.stage_order.join(" | ") : "",
      session.total_stages,
      session.total_trials,
      session.recorded_trials,
      session.user_agent,
      session.page_url,
      trial.stage_name,
      trial.stage_index,
      trial.stage_trial_index,
      trial.stage_trial_count,
      trial.trial_id,
      trial.img_id,
      trial.img_path,
      trial.filter_left,
      trial.filter_right,
      trial.prompt,
      trial.selected_side,
      trial.selected_filter,
      trial.trial_start_timestamp,
      trial.response_timestamp,
      trial.reaction_time_ms,
      receivedAt,
    ]);

    if (rows.length > 0) {
      sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, RESPONSE_HEADERS.length).setValues(rows);
    }

    return jsonResponse_({
      ok: true,
      inserted_rows: rows.length,
      session_id: session.session_id,
    });
  } catch (error) {
    return jsonResponse_({
      ok: false,
      error: error.message,
    });
  }
}

function parsePayload_(e) {
  if (e && e.parameter && e.parameter.payload) {
    return JSON.parse(e.parameter.payload);
  }

  if (e && e.postData && e.postData.contents) {
    const raw = e.postData.contents;

    if (raw.indexOf("payload=") === 0) {
      const params = parseFormEncoded_(raw);
      if (params.payload) {
        return JSON.parse(params.payload);
      }
    }

    return JSON.parse(raw);
  }

  throw new Error("No payload provided.");
}

function parseFormEncoded_(raw) {
  return raw.split("&").reduce(function (accumulator, pair) {
    const parts = pair.split("=");
    const key = decodeURIComponent((parts[0] || "").replace(/\+/g, " "));
    const value = decodeURIComponent((parts.slice(1).join("=") || "").replace(/\+/g, " "));
    accumulator[key] = value;
    return accumulator;
  }, {});
}

function validatePayload_(payload) {
  if (!payload || !payload.session || !Array.isArray(payload.trials)) {
    throw new Error("Payload must include session and trials.");
  }

  if (!payload.session.session_id) {
    throw new Error("session.session_id is required.");
  }
}

function getOrCreateSheet_() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheetName = "responses";
  return spreadsheet.getSheetByName(sheetName) || spreadsheet.insertSheet(sheetName);
}

function ensureHeaders_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(RESPONSE_HEADERS);
  }
}

function jsonResponse_(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
