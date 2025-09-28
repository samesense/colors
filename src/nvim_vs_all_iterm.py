import argparse
import csv
import math
import plistlib
import re
import sys
import time
from io import BytesIO
from urllib.parse import urlparse

import requests

HEX_RE = re.compile(r"#(?:[0-9A-Fa-f]{6})")


def srgb_euclid(c1, c2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1, c2)))


def hex_to_rgb(hexstr):
    hexstr = hexstr.strip()
    if not hexstr.startswith("#") or len(hexstr) != 7:
        return None
    return (int(hexstr[1:3], 16), int(hexstr[3:5], 16), int(hexstr[5:7], 16))


def load_iterm_colors(iterm_url):
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
                colors.append(
                    (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
                )
    return list(dict.fromkeys(colors))


def get_github_default_branch(owner, repo):
    api = f"https://api.github.com/repos/{owner}/{repo}"
    r = requests.get(api, timeout=30)
    r.raise_for_status()
    return r.json().get("default_branch", "main")


def github_tree(owner, repo, branch):
    api = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    r = requests.get(api, timeout=30)
    r.raise_for_status()
    return r.json().get("tree", [])


def fetch_text(url):
    r = requests.get(url, timeout=30)
    if r.status_code == 404 and "/blob/" in url:
        url = url.replace(
            "https://github.com/", "https://raw.githubusercontent.com/"
        ).replace("/blob/", "/")
        r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.text


def is_github_repo(url):
    u = urlparse(url)
    if u.netloc != "github.com":
        return False
    parts = [p for p in u.path.split("/") if p]
    return len(parts) == 2


def is_github_file(url):
    u = urlparse(url)
    if u.netloc == "raw.githubusercontent.com":
        return True
    if u.netloc == "github.com" and "/blob/" in u.path:
        return True
    return False


def load_nvim_colors(nvim_url):
    texts = []
    if is_github_repo(nvim_url):
        owner, repo = [p for p in urlparse(nvim_url).path.split("/") if p]
        branch = get_github_default_branch(owner, repo)
        tree = github_tree(owner, repo, branch)
        candidate_paths = [
            obj["path"]
            for obj in tree
            if obj.get("path", "").lower().endswith((".lua", ".vim"))
            and any(
                seg in obj["path"].lower()
                for seg in (
                    "lua/",
                    "colors/",
                    "themes/",
                    "theme/",
                    "highlight",
                    "palette",
                )
            )
        ]
        if not candidate_paths:
            candidate_paths = [
                obj["path"]
                for obj in tree
                if obj.get("path", "").lower().endswith(".lua")
            ]
        for p in candidate_paths:
            raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{p}"
            try:
                texts.append(fetch_text(raw))
            except Exception:
                pass
        if not texts:
            raise RuntimeError("Could not fetch any theme files from repo.")
    elif is_github_file(nvim_url):
        texts.append(fetch_text(nvim_url))
    else:
        texts.append(fetch_text(nvim_url))

    hexes = set()
    for t in texts:
        hexes.update(HEX_RE.findall(t))
        for m in re.findall(r"0x([0-9A-Fa-f]{6})", t):
            hexes.add("#" + m)

    colors = []
    for h in hexes:
        rgb = hex_to_rgb(h)
        if rgb:
            colors.append(rgb)
    return list(dict.fromkeys(colors))


def avg_nearest_neighbor_distance(p1, p2):
    total = 0.0
    for c in p1:
        total += min(srgb_euclid(c, d) for d in p2)
    return total / max(1, len(p1))


def compare_palettes(iterm_url, nvim_colors):
    iterm = load_iterm_colors(iterm_url)
    d1 = avg_nearest_neighbor_distance(iterm, nvim_colors)
    d2 = avg_nearest_neighbor_distance(nvim_colors, iterm)
    return (d1 + d2) / 2.0


def main():
    ap = argparse.ArgumentParser(
        description="Compare all iTerm themes from CSV vs one Neovim theme."
    )
    ap.add_argument(
        "--csv", required=True, help="CSV file with columns: name,url for iTerm themes"
    )
    ap.add_argument(
        "--nvim", required=True, help="Neovim theme (repo URL or raw file URL)"
    )
    ap.add_argument("--out", default="results.tsv", help="Output TSV file")
    args = ap.parse_args()

    nvim_colors = load_nvim_colors(args.nvim)

    results = []
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name, url = row["name"], row["url"]
            try:
                score = compare_palettes(url, nvim_colors)
                results.append((name, url, score))
                print(f"{name}: {score:.2f}")
            except Exception as e:
                print(f"Skipping {name} ({url}) due to error: {e}", file=sys.stderr)
            time.sleep(0.5)

    # Sort results by best match (lowest score first)
    results.sort(key=lambda x: x[2])

    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["iterm_name", "iterm_url", "similarity_score"])
        writer.writerows(results)


if __name__ == "__main__":
    main()
