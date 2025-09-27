#!/usr/bin/env python3
import argparse
import csv
import re
import time
from urllib.parse import urlparse

import requests

HEX_RE = re.compile(r"#(?:[0-9A-Fa-f]{6})")


def is_github_repo_url(url):
    """Check if the URL looks like github.com/owner/repo"""
    u = urlparse(url)
    parts = [p for p in u.path.split("/") if p]
    return u.netloc == "github.com" and len(parts) == 2


def get_repo_tree(owner, repo):
    """Fetch GitHub repo tree for HEAD"""
    api = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    r = requests.get(api, timeout=20)
    if r.status_code != 200:
        return None, f"API error {r.status_code}"
    return r.json().get("tree", []), None


def fetch_raw_file(owner, repo, path):
    """Fetch raw file text from GitHub repo"""
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}"
    r = requests.get(raw_url, timeout=20)
    if r.status_code == 200:
        return r.text
    return ""


def extract_colors_from_text(text):
    """Find hex colors in file text"""
    hexes = set(HEX_RE.findall(text))
    for m in re.findall(r"0x([0-9A-Fa-f]{6})", text):
        hexes.add("#" + m)
    return sorted(hexes)


def repo_extract_colors(owner, repo):
    """Scan repo for theme files and extract colors"""
    tree, err = get_repo_tree(owner, repo)
    if tree is None:
        return [], err
    colors = set()
    for obj in tree:
        path = obj.get("path", "").lower()
        if path.endswith((".lua", ".vim")) and any(
            seg in path for seg in ("color", "theme", "palette")
        ):
            text = fetch_raw_file(owner, repo, obj["path"])
            colors.update(extract_colors_from_text(text))
    if colors:
        return sorted(colors), "theme file found"
    return [], "no theme files"


def main():
    ap = argparse.ArgumentParser(
        description="Check Neovim theme URLs for compatibility and store colors"
    )
    ap.add_argument("--csv", required=True, help="CSV file with columns: name,url")
    ap.add_argument(
        "--out",
        default="../data/interim/urls/nvim_check_results.tsv",
        help="Output TSV file",
    )
    args = ap.parse_args()

    results = []
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name, url = row["name"], row["url"]
            if not is_github_repo_url(url):
                results.append((name, url, "invalid_repo_url", ""))
                print(f"{name}: {url} -> invalid_repo_url")
                continue

            owner, repo = [p for p in urlparse(url).path.split("/") if p]
            colors, reason = repo_extract_colors(owner, repo)
            status = "compatible" if colors else f"incompatible ({reason})"
            color_str = ",".join(colors)
            results.append((name, url, status, color_str))
            print(f"{name}: {url} -> {status}, {len(colors)} colors found")
            time.sleep(0.5)

    # save results
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["name", "url", "status", "colors"])
        writer.writerows(results)


if __name__ == "__main__":
    main()
