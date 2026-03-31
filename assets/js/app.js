const config = {
  title: "PhoTone",
  instructions: [
    "You will complete two sections of image comparison games.",
    "Select either Left (F) or Right (J) for each trial according to the prompt.",
    "Stage-specific instructions will appear before each section begins.",
    "Your responses and response times will be recorded anonymously.",
    "Click the Start button if you agree to participate.",
  ],
  estimatedTime: "10 minutes",
  stageCsvUrls: {
    arousal: "./experiment/arousal.csv",
    valence: "./experiment/valence.csv",
  },
  stageInstructions: {
    valence: {
      title: "",
      paragraphs: [
        "In this section, choose the image that feels <strong>more positive (pleasant)</strong> in mood. Focus on the overall emotional tone the image conveys.",
        "For example, an image might feel more positive if it appears more cheerful, inviting, or uplifting, rather than gloomy, tense, or unpleasant.",
        "There are no right or wrong answers. Please rely on your immediate impression.",
      ],
    },
    arousal: {
      title: "",
      paragraphs: [
        "In this section, choose the image that feels <strong>more emotionally intense (activated)</strong>. Focus on how strong or impactful the feeling is.",
        "For example, an image may feel more intense if it seems more exciting, dramatic, or striking, while a less intense image may feel more calm, muted, or subdued.",
        "There are no right or wrong answers. Please rely on your immediate impression.",
      ],
    },
  },
  submitMode: "google-apps-script",
  googleAppsScript: {
    payloadField: "payload",
    useNoCors: true,
  },
  submitUrl: "",
  debug: false,
  ...window.STUDY_CONFIG,
};

const state = {
  sessionId: createSessionId(),
  sessionStartedAt: new Date().toISOString(),
  trials: [],
  stageOrder: [],
  responses: [],
  currentTrialIndex: -1,
  currentPresentation: null,
  trialStartEpochMs: 0,
  trialStartIso: "",
  isTransitioning: false,
  isSubmitting: false,
  hasSubmitted: false,
};

const ui = {
  studyTitle: document.querySelector("#study-title"),
  studyInstructions: document.querySelector("#study-instructions"),
  trialCountLabel: document.querySelector("#trial-count-label"),
  submissionLabel: document.querySelector("#submission-label"),
  sessionIdLabel: document.querySelector("#session-id-label"),
  loadStatus: document.querySelector("#load-status"),
  startButton: document.querySelector("#start-button"),
  introScreen: document.querySelector("#intro-screen"),
  stageScreen: document.querySelector("#stage-screen"),
  trialScreen: document.querySelector("#trial-screen"),
  finishScreen: document.querySelector("#finish-screen"),
  stageInstructionsKicker: document.querySelector("#stage-instructions-kicker"),
  stageInstructionsTitle: document.querySelector("#stage-instructions-title"),
  stageInstructionsBody: document.querySelector("#stage-instructions-body"),
  stageInstructionsName: document.querySelector("#stage-instructions-name"),
  stageContinueButton: document.querySelector("#stage-continue-button"),
  progressFill: document.querySelector("#progress-fill"),
  progressTrack: document.querySelector(".progress-track"),
  progressCount: document.querySelector("#progress-count"),
  stageLabel: document.querySelector("#stage-label"),
  promptText: document.querySelector("#prompt-text"),
  leftFigure: document.querySelector("#left-figure"),
  rightFigure: document.querySelector("#right-figure"),
  leftImage: document.querySelector("#left-image"),
  rightImage: document.querySelector("#right-image"),
  leftButton: document.querySelector("#left-button"),
  rightButton: document.querySelector("#right-button"),
  stimulusGrid: document.querySelector("#stimulus-grid"),
  recordedCount: document.querySelector("#recorded-count"),
  finishMessage: document.querySelector("#finish-message"),
  submissionStatus: document.querySelector("#submission-status"),
  submissionStatusText: document.querySelector("#submission-status-text"),
  submitButton: document.querySelector("#submit-button"),
  retryButton: document.querySelector("#retry-button"),
  exportButton: document.querySelector("#export-button"),
  uploadModal: document.querySelector("#upload-modal"),
  uploadMessage: document.querySelector("#upload-message"),
};

bootstrap().catch((error) => {
  console.error(error);
  setLoadStatus("error", `Unable to initialize study: ${error.message}`);
});

async function bootstrap() {
  applyConfig();
  bindEvents();

  const parsedTrials = await loadStudyTrials();

  if (!parsedTrials.length) {
    throw new Error("No study trials were found in the configured stage CSV files.");
  }

  state.trials = parsedTrials;

  ui.trialCountLabel.textContent = `${parsedTrials.length} loaded`;
  ui.recordedCount.textContent = String(state.responses.length);
  setLoadStatus(
    "ready",
    `Loaded ${parsedTrials.length} trials across ${state.stageOrder.length} stages. Ready to begin.`
  );
  ui.startButton.disabled = false;

  debug("Loaded trials", parsedTrials);
}

function applyConfig() {
  document.title = config.title;
  ui.studyTitle.textContent = config.title;
  ui.studyInstructions.innerHTML = config.instructions
    .map((line) => `<p>${line}</p>`)
    .join("");
  ui.sessionIdLabel.textContent = state.sessionId;
  ui.submissionLabel.textContent = config.estimatedTime;
}

function bindEvents() {
  ui.startButton.addEventListener("click", startStudy);
  ui.stageContinueButton.addEventListener("click", startStage);
  ui.leftButton.addEventListener("click", () => handleChoice("left"));
  ui.rightButton.addEventListener("click", () => handleChoice("right"));
  ui.submitButton.addEventListener("click", submitResults);
  ui.retryButton.addEventListener("click", submitResults);
  ui.exportButton.addEventListener("click", downloadBackup);
  window.addEventListener("keydown", handleKeyResponse);
  window.addEventListener("beforeunload", handleBeforeUnload);
}

function startStudy() {
  state.currentTrialIndex = 0;
  state.responses = [];
  state.hasSubmitted = false;
  ui.recordedCount.textContent = "0";
  showStageInstructions();
}

function startStage() {
  showScreen("trial");
  renderTrial();
}

function renderTrial() {
  const trial = state.trials[state.currentTrialIndex];

  if (!trial) {
    showFinishScreen();
    return;
  }

  const leftCandidate = {
    side: "left",
    filter: trial.filter_left,
  };
  const rightCandidate = {
    side: "right",
    filter: trial.filter_right,
  };

  state.currentPresentation = {
    trial,
    left: leftCandidate,
    right: rightCandidate,
  };
  state.trialStartEpochMs = performance.now();
  state.trialStartIso = new Date().toISOString();

  renderCandidate(ui.leftFigure, ui.leftImage, leftCandidate.filter, trial);
  renderCandidate(ui.rightFigure, ui.rightImage, rightCandidate.filter, trial);
  ui.promptText.textContent = trial.prompt;
  ui.stageLabel.textContent = `Stage ${trial.stage_index} of ${state.stageOrder.length}`;

  ui.leftButton.disabled = false;
  ui.rightButton.disabled = false;
  ui.leftButton.classList.remove("is-selected");
  ui.rightButton.classList.remove("is-selected");
  ui.stimulusGrid.classList.remove("is-locked");

  const currentHumanIndex = state.currentTrialIndex + 1;
  const totalTrials = state.trials.length;
  const percent = Math.round((state.currentTrialIndex / totalTrials) * 100);

  ui.progressFill.style.width = `${percent}%`;
  ui.progressTrack.setAttribute("aria-valuenow", String(percent));
  ui.progressCount.textContent = `${currentHumanIndex} / ${totalTrials}`;
}

function renderCandidate(figureEl, imgEl, filterName, trial) {
  figureEl.className = `filter-frame ${filterName}`;
  imgEl.src = resolveAssetPath(trial.img_path);
  imgEl.alt = `${filterName} version of stimulus ${trial.img_id}`;
  imgEl.dataset.filter = filterName;
}

function handleKeyResponse(event) {
  if (ui.trialScreen.hidden || state.isTransitioning || !state.currentPresentation) {
    return;
  }

  if (event.repeat) {
    return;
  }

  const key = event.key.toLowerCase();

  if (key === "f" && !ui.leftButton.disabled) {
    event.preventDefault();
    handleChoice("left");
  }

  if (key === "j" && !ui.rightButton.disabled) {
    event.preventDefault();
    handleChoice("right");
  }
}

function handleChoice(side) {
  if (state.isTransitioning || !state.currentPresentation) {
    return;
  }

  state.isTransitioning = true;

  const responseTimestamp = new Date().toISOString();
  const reactionTimeMs = Math.round(performance.now() - state.trialStartEpochMs);
  const selectedCandidate =
    side === "left" ? state.currentPresentation.left : state.currentPresentation.right;

  const response = {
    session_id: state.sessionId,
    stage_name: state.currentPresentation.trial.stage_name,
    stage_index: state.currentPresentation.trial.stage_index,
    stage_trial_index: state.currentPresentation.trial.stage_trial_index,
    stage_trial_count: state.currentPresentation.trial.stage_trial_count,
    trial_id: state.currentPresentation.trial.trial_id,
    img_id: state.currentPresentation.trial.img_id,
    img_path: state.currentPresentation.trial.img_path,
    filter_left: state.currentPresentation.trial.filter_left,
    filter_right: state.currentPresentation.trial.filter_right,
    prompt: state.currentPresentation.trial.prompt,
    selected_side: side,
    selected_filter: selectedCandidate.filter,
    trial_start_timestamp: state.trialStartIso,
    response_timestamp: responseTimestamp,
    reaction_time_ms: reactionTimeMs,
  };

  state.responses.push(response);
  ui.recordedCount.textContent = String(state.responses.length);

  const selectedButton = side === "left" ? ui.leftButton : ui.rightButton;
  selectedButton.classList.add("is-selected");
  ui.leftButton.disabled = true;
  ui.rightButton.disabled = true;
  ui.stimulusGrid.classList.add("is-locked");

  debug("Recorded response", response);

  window.setTimeout(() => {
    state.currentTrialIndex += 1;
    state.isTransitioning = false;
    proceedToNextStep();
  }, 350);
}

function showFinishScreen() {
  const payload = buildResultsPayload();
  showScreen("finish");

  ui.progressFill.style.width = "100%";
  ui.progressTrack.setAttribute("aria-valuenow", "100");
  ui.submissionStatusText.textContent = config.submitUrl ? "Pending" : "Export only";

  if (config.submitUrl) {
    setSubmissionStatus("loading", "All trials are complete. Uploading results now...");
    ui.finishMessage.textContent =
      "All responses are recorded. The results are uploading automatically. Please keep this tab open until submission finishes.";
    ui.submitButton.hidden = true;
    showUploadModal("Results are uploading. Please wait...");
    void submitResults({ auto: true });
  } else {
    setSubmissionStatus(
      "warning",
      "No submit URL is configured. Use the JSON backup button to save the session data."
    );
    ui.finishMessage.textContent =
      "No backend endpoint is configured in assets/js/config.js. You can still download the study data as JSON.";
    ui.submitButton.hidden = true;
  }

  ui.retryButton.hidden = true;
  ui.exportButton.disabled = false;

  debug("Final payload", payload);
}

async function submitResults(options = {}) {
  const { auto = false } = options;
  const payload = buildResultsPayload();

  if (!config.submitUrl) {
    setSubmissionStatus(
      "warning",
      "Submission skipped because no submit URL is configured. Download the JSON backup instead."
    );
    return;
  }

  state.isSubmitting = true;
  ui.submitButton.disabled = true;
  ui.retryButton.disabled = true;
  setSubmissionStatus("loading", "Submitting results to the backend endpoint...");
  ui.submissionStatusText.textContent = "Submitting";
  showUploadModal("Results are uploading. Please wait...");

  try {
    await submitPayload(payload);

    state.hasSubmitted = true;
    hideUploadModal();
    setSubmissionStatus("success", "Results submitted successfully.");
    ui.submissionStatusText.textContent = "Submitted";
    ui.finishMessage.textContent =
      "Results were submitted successfully. You may also download a local backup if needed.";
    ui.retryButton.hidden = true;
  } catch (error) {
    console.error(error);
    hideUploadModal();
    setSubmissionStatus(
      "error",
      `Submission failed: ${error.message}. Retry now or download the JSON backup.`
    );
    ui.submissionStatusText.textContent = "Failed";
    ui.finishMessage.textContent =
      "Automatic upload did not finish successfully. Retry the submission or download the JSON backup before leaving this page.";
    ui.retryButton.hidden = false;
    ui.retryButton.disabled = false;
  } finally {
    state.isSubmitting = false;
    ui.submitButton.disabled = state.hasSubmitted;
    if (auto && !state.hasSubmitted) {
      ui.submitButton.hidden = true;
    }
  }
}

async function submitPayload(payload) {
  if (config.submitMode === "google-apps-script") {
    return submitToGoogleAppsScript(payload);
  }

  const response = await fetch(config.submitUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Submission failed with HTTP ${response.status}`);
  }

  return response;
}

function buildResultsPayload() {
  return {
    session: {
      session_id: state.sessionId,
      started_at: state.sessionStartedAt,
      completed_at: new Date().toISOString(),
      stage_order: state.stageOrder.map(formatStageName),
      total_stages: state.stageOrder.length,
      total_trials: state.trials.length,
      recorded_trials: state.responses.length,
      user_agent: navigator.userAgent,
      page_url: window.location.href,
    },
    trials: state.responses,
  };
}

async function submitToGoogleAppsScript(payload) {
  const gasConfig = {
    payloadField: "payload",
    useNoCors: true,
    ...config.googleAppsScript,
  };
  const body = new URLSearchParams({
    [gasConfig.payloadField]: JSON.stringify(payload),
  });
  const requestOptions = {
    method: "POST",
    body,
  };

  if (gasConfig.useNoCors) {
    requestOptions.mode = "no-cors";
  }

  const response = await fetch(config.submitUrl, requestOptions);

  // Apps Script web apps are commonly called from static sites with no-cors,
  // which produces an opaque response even on success.
  if (gasConfig.useNoCors) {
    return response;
  }

  if (!response.ok) {
    throw new Error(`Submission failed with HTTP ${response.status}`);
  }

  return response;
}

function downloadBackup() {
  const payload = buildResultsPayload();
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `photone-session-${state.sessionId}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

function showScreen(name) {
  const screens = {
    intro: ui.introScreen,
    stage: ui.stageScreen,
    trial: ui.trialScreen,
    finish: ui.finishScreen,
  };

  Object.entries(screens).forEach(([screenName, screenEl]) => {
    const isActive = screenName === name;
    screenEl.hidden = !isActive;
    screenEl.classList.toggle("screen-active", isActive);
  });
}

function setLoadStatus(kind, message) {
  ui.loadStatus.dataset.status = kind;
  ui.loadStatus.textContent = message;
}

function setSubmissionStatus(kind, message) {
  ui.submissionStatus.dataset.status = kind;
  ui.submissionStatus.textContent = message;
}

function showUploadModal(message) {
  ui.uploadMessage.textContent = message;
  ui.uploadModal.hidden = false;
  document.body.classList.add("modal-open");
}

function hideUploadModal() {
  ui.uploadModal.hidden = true;
  document.body.classList.remove("modal-open");
}

function showStageInstructions() {
  const trial = state.trials[state.currentTrialIndex];

  if (!trial) {
    showFinishScreen();
    return;
  }

  const stageConfig = config.stageInstructions?.[trial.stage_name] ?? {
      title: "Stage instructions",
      paragraphs: [
        "Choose the image that best matches the prompt for this section.",
        "There are no right or wrong answers. Please rely on your immediate impression.",
    ],
  };

  ui.stageInstructionsKicker.textContent =
    `Stage ${trial.stage_index} of ${state.stageOrder.length}`;
  ui.stageInstructionsTitle.textContent = stageConfig.title;
  ui.stageInstructionsName.textContent = `Section ${trial.stage_index}`;
  ui.stageInstructionsBody.innerHTML = stageConfig.paragraphs
    .map((paragraph) => `<p>${paragraph}</p>`)
    .join("");

  showScreen("stage");
}

function proceedToNextStep() {
  const nextTrial = state.trials[state.currentTrialIndex];

  if (!nextTrial) {
    showFinishScreen();
    return;
  }

  const previousTrial = state.trials[state.currentTrialIndex - 1];

  if (!previousTrial || previousTrial.stage_index !== nextTrial.stage_index) {
    showStageInstructions();
    return;
  }

  renderTrial();
}

function createSessionId() {
  if (crypto.randomUUID) {
    return crypto.randomUUID();
  }

  return `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function resolveAssetPath(pathValue) {
  return new URL(pathValue.trim(), window.location.href).toString();
}

async function fetchText(url) {
  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to load ${url} (HTTP ${response.status})`);
  }

  return response.text();
}

async function loadStudyTrials() {
  const stageEntries = Object.entries(config.stageCsvUrls ?? {});

  if (!stageEntries.length) {
    throw new Error("No stage CSV files are configured.");
  }

  const loadedStages = await Promise.all(
    stageEntries.map(async ([stageName, url]) => {
      const csvText = await fetchText(url);
      const parsedTrials = parseTrialCsv(csvText);
      return { stageName, parsedTrials };
    })
  );

  const shuffledStages = shuffleArray(loadedStages);
  state.stageOrder = shuffledStages.map((stage) => stage.stageName);

  return shuffledStages.flatMap((stage, stageIndex) => {
    const shuffledTrials = shuffleArray(stage.parsedTrials);

    return shuffledTrials.map((trial, trialIndex) => ({
      ...trial,
      stage_name: stage.stageName,
      stage_index: stageIndex + 1,
      stage_trial_index: trialIndex + 1,
      stage_trial_count: shuffledTrials.length,
    }));
  });
}

function parseTrialCsv(csvText) {
  const rows = parseCsvRows(csvText).filter((row) => row.some((cell) => cell.trim() !== ""));

  if (rows.length < 2) {
    return [];
  }

  const [headerRow, ...dataRows] = rows;
  const normalizedHeaders = headerRow.map((cell) => normalizeCell(cell));

  return dataRows.map((row, index) => {
    const record = {};

    normalizedHeaders.forEach((header, headerIndex) => {
      record[header] = normalizeCell(row[headerIndex] ?? "");
    });

    const missing = ["trial_id", "img_id", "img_path", "filter_left", "filter_right", "prompt"]
      .filter((key) => !record[key]);

    if (missing.length) {
      throw new Error(`Trial row ${index + 2} is missing: ${missing.join(", ")}`);
    }

    return record;
  });
}

function parseCsvRows(csvText) {
  const rows = [];
  let currentCell = "";
  let currentRow = [];
  let inQuotes = false;

  for (let index = 0; index < csvText.length; index += 1) {
    const char = csvText[index];
    const nextChar = csvText[index + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        currentCell += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (char === "," && !inQuotes) {
      currentRow.push(currentCell);
      currentCell = "";
      continue;
    }

    if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && nextChar === "\n") {
        index += 1;
      }
      currentRow.push(currentCell);
      rows.push(currentRow);
      currentCell = "";
      currentRow = [];
      continue;
    }

    currentCell += char;
  }

  if (currentCell.length || currentRow.length) {
    currentRow.push(currentCell);
    rows.push(currentRow);
  }

  return rows;
}

function normalizeCell(value) {
  return value.trim().replace(/^"(.*)"$/, "$1").trim();
}

function debug(...args) {
  if (config.debug) {
    console.debug("[PhoTone]", ...args);
  }
}

function handleBeforeUnload(event) {
  if (!state.isSubmitting) {
    return;
  }

  event.preventDefault();
  event.returnValue = "";
}

function formatStageName(value) {
  return value.replace(/[-_]/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function shuffleArray(values) {
  const copy = [...values];

  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swapIndex]] = [copy[swapIndex], copy[index]];
  }

  return copy;
}
