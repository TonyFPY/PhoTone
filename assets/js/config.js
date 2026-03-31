window.STUDY_CONFIG = {
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
        "<strong>For example, an image might feel more positive if it appears more cheerful, inviting, or uplifting, rather than gloomy, tense, or unpleasant.</strong>",
        "There are no right or wrong answers. Please rely on your immediate impression.",
      ],
    },
    arousal: {
      title: "",
      paragraphs: [
        "In this section, choose the image that feels <strong>more emotionally intense (activated)</strong>. Focus on how strong or impactful the feeling is.",
        "<strong>For example, an image may feel more intense if it seems more exciting, dramatic, or striking, while a less intense image may feel more calm, muted, or subdued.</strong>",
        "There are no right or wrong answers. Please rely on your immediate impression.",
      ],
    },
  },
  submitMode: "google-apps-script",
  googleAppsScript: {
    payloadField: "payload",
    useNoCors: true,
  },
  submitUrl: "https://script.google.com/macros/s/AKfycbyQordp-KF5zWJVpCO0aGgA86Mm_1JOtqOD9BTJGBFaTPSuZAyxw8jHhroBJ4kqNkmsqA/exec",
  debug: false,
};
