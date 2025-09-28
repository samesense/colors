import argparse
import csv
import math

import numpy as np

if not hasattr(np, "asscalar"):
    np.asscalar = lambda x: x.item()

from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor


# ---------- Conversion ----------
def hex_to_rgb(hexstr):
    return (int(hexstr[1:3], 16), int(hexstr[3:5], 16), int(hexstr[5:7], 16))


def rgb_to_lab(rgb):
    r, g, b = rgb
    rgb = sRGBColor(r, g, b, is_upscaled=True)
    return convert_color(rgb, LabColor)


# ---------- Distance metrics ----------
def srgb_euclid(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def avg_nearest_neighbor(p1, p2, dist_fn):
    total = 0.0
    for c1 in p1:
        total += min(dist_fn(c1, c2) for c2 in p2)
    return total / max(1, len(p1))


def symmetric_distance(p1, p2, dist_fn):
    return (
        avg_nearest_neighbor(p1, p2, dist_fn) + avg_nearest_neighbor(p2, p1, dist_fn)
    ) / 2.0


def lab_distance(c1, c2):
    return delta_e_cie2000(c1, c2)


# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(
        description="Compare stored Neovim and iTerm theme colors (TSV files)."
    )
    ap.add_argument(
        "--nvim",
        required=True,
        help="TSV file with Neovim colors (name,url,status,colors)",
    )
    ap.add_argument(
        "--iterm", required=True, help="TSV file with iTerm colors (name,url,colors)"
    )
    ap.add_argument("--out", default="results.tsv", help="Output TSV file")
    args = ap.parse_args()

    # Load Neovim themes
    nvim_themes = []
    with open(args.nvim, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if not row.get("colors"):
                continue
            colors = [c for c in row["colors"].split(",") if c]
            rgbs = [hex_to_rgb(c) for c in colors]
            labs = [rgb_to_lab(c) for c in rgbs]
            nvim_themes.append(
                {
                    "name": row["name"],
                    "url": row["url"],
                    "rgbs": rgbs,
                    "labs": labs,
                }
            )

    # Load iTerm themes
    iterm_themes = []
    with open(args.iterm, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if not row.get("colors"):
                continue
            colors = [c for c in row["colors"].split(",") if c]
            rgbs = [hex_to_rgb(c) for c in colors]
            labs = [rgb_to_lab(c) for c in rgbs]
            iterm_themes.append(
                {
                    "name": row["name"],
                    "url": row["url"],
                    "rgbs": rgbs,
                    "labs": labs,
                }
            )

    # Compare all pairs
    results = []
    for nvim in nvim_themes:
        for iterm in iterm_themes:
            # RGB
            rgb_score = symmetric_distance(nvim["rgbs"], iterm["rgbs"], srgb_euclid)
            rgb_norm = max(0.0, min(1.0, 1 - (rgb_score / 441.0)))

            # Lab
            lab_score = symmetric_distance(nvim["labs"], iterm["labs"], lab_distance)
            lab_norm = max(0.0, min(1.0, 1 - (lab_score / 100.0)))

            results.append(
                (
                    nvim["name"],
                    iterm["name"],
                    iterm["url"],
                    rgb_score,
                    lab_score,
                    rgb_norm,
                    lab_norm,
                )
            )

    # Sort by best perceptual match
    results.sort(key=lambda x: -x[6])

    # Save results
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(
            [
                "nvim_name",
                "iterm_name",
                "iterm_url",
                "similarity_score_rgb",
                "similarity_score_lab",
                "similarity_index_rgb",
                "similarity_index_lab",
            ]
        )
        writer.writerows(results)


if __name__ == "__main__":
    main()
