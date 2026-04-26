#!/usr/bin/env python3
"""Run the consolidated PhoTone publication-analysis pipeline.

How to execute:
    python analysis/scripts/run_all.py

Optional arguments:
    python analysis/scripts/run_all.py --input analysis/results/results.csv --outdir analysis/results --topn 8 --boots 300

What this script does:
    - Executes the consolidated publication-quality script.
    - Stops on failure with a non-zero exit code.
"""

from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="analysis/results/results.csv")
    parser.add_argument("--outdir", default="analysis/results")
    parser.add_argument("--topn", type=int, default=8)
    parser.add_argument("--boots", type=int, default=300)
    args = parser.parse_args()

    scripts = [
        [
            "analysis/scripts/07_fancy_visualizations.py",
            "--input",
            args.input,
            "--outdir",
            args.outdir,
            "--topn",
            str(args.topn),
            "--boots",
            str(args.boots),
        ]
    ]

    for script_cmd in scripts:
        cmd = [sys.executable, *script_cmd]
        print("Running:", " ".join(cmd))
        subprocess.run(cmd, check=True)

    print("All analyses completed.")


if __name__ == "__main__":
    main()
