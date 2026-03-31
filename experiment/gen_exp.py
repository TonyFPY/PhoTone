import os
import csv
import glob
import random
from itertools import combinations

filter_names = [
    "filter-lark",
    "filter-sutro",
    "filter-hudson",
    "filter-1977",
    "filter-lofi",
    "filter-gingham",
    "filter-juno",
    "filter-inkwell",  
    "filter-moon",
    "filter-clarendon"
]

head_names = ["trial_id", "img_id", "img_path", "filter_left", "filter_right", "prompt"]
prompt_options = [
    "positive (pleasant)",
    "activated (emotionally intense)"
]
BASE_DIR = os.path.dirname(__file__)
image_dir = os.path.join(BASE_DIR, "..", "images")
image_names = glob.glob(os.path.join(image_dir, "*.jpg"))


def _extract_img_id(img_path):
    return os.path.splitext(os.path.basename(img_path))[0]


def _to_web_img_path(img_path):
    return f"./images/{os.path.basename(img_path)}"


def _choose_orientation(filter_a, filter_b, side_counts):
    # Pick the orientation that keeps left/right totals closest for the two filters.
    left_a_score = abs((side_counts[filter_a]["left"] + 1) - side_counts[filter_a]["right"])
    right_b_score = abs(side_counts[filter_b]["left"] - (side_counts[filter_b]["right"] + 1))
    score_ab = left_a_score + right_b_score

    left_b_score = abs((side_counts[filter_b]["left"] + 1) - side_counts[filter_b]["right"])
    right_a_score = abs(side_counts[filter_a]["left"] - (side_counts[filter_a]["right"] + 1))
    score_ba = left_b_score + right_a_score

    if score_ab < score_ba:
        return filter_a, filter_b
    if score_ba < score_ab:
        return filter_b, filter_a

    if random.random() < 0.5:
        return filter_a, filter_b
    return filter_b, filter_a


def _build_balanced_image_pool(images, total_trials):
    if not images:
        raise ValueError("No images found in image_names.")

    pool = []
    while len(pool) < total_trials:
        cycle = list(images)
        random.shuffle(cycle)
        pool.extend(cycle)

    return pool[:total_trials]


def generate_trials(filters, prompts, images):
    if len(filters) < 2:
        raise ValueError("Need at least two filters to make unique unordered pairs.")
    if not prompts:
        raise ValueError("prompt_options must not be empty.")
    side_counts = {name: {"left": 0, "right": 0} for name in filters}
    combos = []

    for filter_a, filter_b in combinations(filters, 2):
        for prompt in prompts:
            combos.append((filter_a, filter_b, prompt))

    random.shuffle(combos)
    image_pool = _build_balanced_image_pool(images, len(combos))

    trials = []
    for trial_id, ((filter_a, filter_b, prompt), img_path) in enumerate(
        zip(combos, image_pool), start=1
    ):
        filter_left, filter_right = _choose_orientation(filter_a, filter_b, side_counts)
        side_counts[filter_left]["left"] += 1
        side_counts[filter_right]["right"] += 1

        trials.append(
            {
                "trial_id": trial_id,
                "img_id": _extract_img_id(img_path),
                "img_path": _to_web_img_path(img_path),
                "filter_left": filter_left,
                "filter_right": filter_right,
                "prompt": prompt,
            }
        )

    random.shuffle(trials)
    for idx, trial in enumerate(trials, start=1):
        trial["trial_id"] = idx

    return trials


def write_trials_csv(trials, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=head_names)
        writer.writeheader()
        writer.writerows(trials)


def main():
    random.seed()
    output_dir = BASE_DIR
    prompt_to_output = {
        "positive (pleasant)": "valence.csv",
        "activated (emotionally intense)": "arousal.csv",
    }

    for prompt in prompt_options:
        if prompt not in prompt_to_output:
            raise ValueError(f"No output file mapping configured for prompt: {prompt}")

        trials = generate_trials(filter_names, [prompt], image_names)
        output_path = os.path.join(output_dir, prompt_to_output[prompt])
        write_trials_csv(trials, output_path)
        print(f"Generated {len(trials)} trials -> {output_path}")


if __name__ == "__main__":
    main()
