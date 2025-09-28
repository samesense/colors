import argparse
import csv
import math
import numpy as np
from skimage.color import rgb2lab, deltaE_ciede2000
from concurrent.futures import ProcessPoolExecutor, as_completed


# ---------- Conversion ----------
def hex_to_rgb(hexstr):
    """#RRGGBB -> (R,G,B) tuple"""
    return (int(hexstr[1:3], 16), int(hexstr[3:5], 16), int(hexstr[5:7], 16))


def rgb_list_to_lab(rgb_list):
    """Convert list of (R,G,B) to Lab array"""
    arr = np.array(rgb_list, dtype=float).reshape(-1, 1, 3) / 255.0
    return rgb2lab(arr).reshape(-1, 3)


# ---------- Distance metrics ----------
def srgb_euclid(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def symmetric_distance_rgb(p1, p2):
    """Symmetric average nearest-neighbor distance in sRGB"""
    p1 = np.array(p1, dtype=float)
    p2 = np.array(p2, dtype=float)
    dists = np.sqrt(((p1[:, None, :] - p2[None, :, :]) ** 2).sum(axis=2))
    d1 = np.min(dists, axis=1).mean()
    d2 = np.min(dists, axis=0).mean()
    return (d1 + d2) / 2.0


def symmetric_distance_lab(lab1, lab2):
    """Symmetric average nearest-neighbor distance in Lab using ΔE2000"""
    dists = np.empty((len(lab1), len(lab2)))
    for i, c1 in enumerate(lab1):
        dists[i] = deltaE_ciede2000(c1[np.newaxis, :], lab2)
    d1 = np.min(dists, axis=1).mean()
    d2 = np.min(dists, axis=0).mean()
    return (d1 + d2) / 2.0


# ---------- Worker ----------
def compare_one_nvim(nvim, iterm_themes):
    results = []
    for iterm in iterm_themes:
        # RGB distance
        rgb_score = symmetric_distance_rgb(nvim["rgbs"], iterm["rgbs"])
        rgb_norm = max(0.0, min(1.0, 1 - (rgb_score / 441.0)))

        # Lab distance (ΔE2000)
        lab_score = symmetric_distance_lab(nvim["labs"], iterm["labs"])
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
    return results


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
    ap.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers (default = num cores)",
    )
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
            labs = rgb_list_to_lab(rgbs)
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
            labs = rgb_list_to_lab(rgbs)
            iterm_themes.append(
                {
                    "name": row["name"],
                    "url": row["url"],
                    "rgbs": rgbs,
                    "labs": labs,
                }
            )

    # Run in parallel
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(compare_one_nvim, nvim, iterm_themes): nvim
            for nvim in nvim_themes
        }
        for future in as_completed(futures):
            results.extend(future.result())

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
