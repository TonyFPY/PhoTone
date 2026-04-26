# PhoTone Experiment Setup

## Overview

This study uses a two-stage, within-subject, two-alternative forced-choice (2AFC) design to evaluate how image filters influence perceived emotional tone. Each participant completes both stages:

1. Valence: select the filtered image that appears more positive (pleasant).
2. Arousal: select the filtered image that appears more emotionally intense (activated).

In every trial, participants view two filtered versions of the same base image, presented side-by-side (left and right), and choose one option using mouse/touch input or keyboard shortcuts (F for left, J for right).

## Procedure

Participants first see study instructions, then complete two experimental blocks (valence and arousal), and finally reach a completion/submission screen.

For each trial:

1. One base image is shown twice, once with each filter from a filter pair.
2. The participant selects the preferred option according to the active stage prompt.
3. The app records choice, timing, and trial metadata.

## Experimental Design Controls

The setup includes the following control mechanisms:

1. Block order randomization:
	The order of the two stages (valence first vs arousal first) is randomized per participant at runtime.
2. Within-block trial randomization:
	Trial order is shuffled independently inside each stage before presentation.
3. Left/right filter balancing:
	During trial generation, filter orientation is chosen with a balancing heuristic that minimizes left-right count imbalance across filters. Ties are broken randomly.

## Stimuli Construction

Trials are generated from all unordered filter combinations applied to the image set.

1. Number of filters: 10
2. Unique unordered pairs per stage: C(10, 2) = 45
3. Prompt-specific CSV generation:
	- One CSV for valence trials
	- One CSV for arousal trials
4. Image distribution:
	Base images are cycled through a shuffled pool so comparisons are distributed across available images.

This produces:

1. 45 trials in valence
2. 45 trials in arousal
3. 90 total trials per participant

## Filters Used

The experiment uses the following 10 filter classes:

1. filter-lark
2. filter-sutro
3. filter-hudson
4. filter-1977
5. filter-lofi
6. filter-gingham
7. filter-juno
8. filter-inkwell
9. filter-moon
10. filter-clarendon

## Stage Prompts

1. Valence stage prompt: "positive (pleasant)"
2. Arousal stage prompt: "activated (emotionally intense)"

## Recorded Measures

Each trial logs behavioral response and metadata, including:

1. selected side and selected filter
2. reaction time (milliseconds)
3. trial identifiers and stimulus metadata (trial id, image id/path, left/right filters, prompt)
4. stage context (stage name/index, trial index within stage, stage trial count)
5. timing stamps (trial start and response timestamps)

At the session level, the payload includes:

1. session id
2. session start and completion times
3. stage order
4. total stages, total trials, and recorded trials
5. user agent and page URL

## Data Submission and Fallback

After the final trial, the app builds a session payload and automatically attempts submission to a Google Apps Script web endpoint.

If submission succeeds, the session is marked as submitted. If submission fails, participants are given two recovery options:

1. retry submission from the finish screen
2. download a JSON backup of the full payload locally

This design supports static web deployment while preserving a participant-safe fallback path for data recovery.


## Analysis

Below is a concise, publication-ready analysis and visualization plan. It is framed to be methodologically defensible, aligned with the design, and suitable for an HCI paper.

### 1. Estimating Perceptual Effects of Filters

We model pairwise choices using a Bradley-Terry framework (or equivalent logistic model) separately for the valence and arousal stages. Each trial contributes a binary outcome indicating which filter is preferred. This yields a latent perceptual score for each filter along both dimensions.

**Outcome**

- Ranked list of filters for valence and arousal
- Effect sizes with uncertainty (confidence intervals)

**Visualization**

- Ranked bar plots with confidence intervals, one per dimension
- Pairwise win-probability heatmap (filters x filters), ordered by latent scores

### 2. Constructing a Valence-Arousal Perceptual Space

To examine the relationship between emotional dimensions, we combine filter scores from both models into a 2D representation.

**Outcome**

- Each filter positioned in a valence-arousal space
- Correlation between dimensions

**Visualization**

- 2D scatter plot (V-A map) with labeled filters and uncertainty, such as error bars or ellipses

### 3. Consistency Across Participants

We evaluate whether perceptual effects are shared across users by measuring agreement in pairwise judgments.

**Methods**

- Compute agreement rates for identical comparisons across participants
- Assess stability of filter rankings via resampling or split-half analysis

**Outcome**

- Quantitative measure of inter-participant consistency
- Confidence in the robustness of inferred filter structure

**Visualization**

- Distribution of agreement rates, either histogram or density plot
- Optional per-filter variability plot

### 4. Validity Checks and Controls

To ensure the observed effects are not artifacts of the experimental setup:

#### 4.1 Image-Level Confounds

- Assess whether filter rankings are consistent across different base images

**Visualization**

- Faceted ranking plots by image, or a variance summary

#### 4.2 Position Bias

- Verify balanced left/right selection rates

**Visualization**

- Simple proportion plot showing left versus right choices

#### 4.3 Reaction Time, Exploratory

- Analyze the relationship between decision difficulty, defined as score difference, and response time

**Visualization**

- Optional scatter plot of score difference versus reaction time

### Final Figure Set (Recommended)

A minimal, publishable set of figures:

1. Valence-Arousal Map, the primary figure
2. Filter Rankings with Confidence Intervals for valence and arousal
3. Pairwise Win-Probability Heatmap
4. Agreement / Consistency Plot

**Optional if space permits**

- Image-level robustness check

### Framing of Contribution

This analysis supports three core claims:

1. Systematic perceptual effects: low-level visual filters produce measurable shifts in perceived valence and arousal.
2. Shared perceptual structure: these effects exhibit non-trivial agreement across participants.
3. Multidimensional organization: filters occupy a structured space in the valence-arousal framework rather than a single perceptual axis.

### Notes on Interpretation

- Results should be framed as perceptual associations, not causal emotional effects.
- Findings are conditional on the stimulus set and filter implementations.
- Aggregation across participants is necessary due to sparse pairwise observations per user.

This plan is sufficient to produce a coherent, credible empirical story that meets expectations for an HCI study: clear methodology, interpretable outputs, and appropriately scoped claims.