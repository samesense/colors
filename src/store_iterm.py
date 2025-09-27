#!/usr/bin/env python3
import argparse
import csv
import plistlib
from io import BytesIO

import requests


def load_iterm_colors(iterm_url):
    """Fetch and parse colors from an .itermcolors file"""
    r = requests.get(iterm_url, timeout=30)
    r.raise_for_status()
    plist = plistlib.load(BytesIO(r.content))
    colors = []
    for v in plist.values():
        if isinstance(v, dict):
            r = v.get("Red Component")
            g = v.get("Green Component")
            b = v.get("Blue Component")
            if (
                isinstance(r, (int, float))
                and isinstance(g, (int, float))
                and isinstance(b, (int, float))
            ):
                R = int(round(r * 255))
                G = int(round(g * 255))
                B = int(round(b * 255))
                colors.append(f"#{R:02X}{G:02X}{B:02X}")
    # de-dup, keep order
    return list(dict.fromkeys(colors))


def main():
    ap = argparse.ArgumentParser(
        description="Extract hex colors from iTerm themes in CSV"
    )
    ap.add_argument("--csv", required=True, help="CSV file with columns: name,url")
    ap.add_argument(
        "--out", default="../data/interim/iterm_colors.tsv", help="Output TSV file"
    )
    args = ap.parse_args()

    results = []
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name, url = row["name"], row["url"]
            try:
                colors = load_iterm_colors(url)
                color_str = ",".join(colors)
                results.append((name, url, color_str))
                print(f"{name}: {len(colors)} colors")
            except Exception as e:
                print(f"Skipping {name} ({url}) due to error: {e}")
                results.append((name, url, ""))

    # save TSV
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["name", "url", "colors"])
        writer.writerows(results)


if __name__ == "__main__":
    main()
