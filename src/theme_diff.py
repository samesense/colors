#!/usr/bin/env python3
import argparse
import base64
import json
import math
import os
import plistlib
import re
import sys
from io import BytesIO
from urllib.parse import urlparse

import requests

HEX_RE = re.compile(r"#(?:[0-9A-Fa-f]{6})")


def srgb_euclid(c1, c2):
    # Euclidean distance in sRGB space
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
    # iTerm files have keys like "Ansi 0 Color", each a dict with float 0..1 components
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
    # de-dup
    colors = list(dict.fromkeys(colors))
    if not colors:
        raise RuntimeError("No colors parsed from iTerm theme.")
    return colors


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
        # convert blob -> raw
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
    return len(parts) == 2  # owner/repo


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
        # enumerate repo files and grab Lua/Vim files that likely contain colors
        owner, repo = [p for p in urlparse(nvim_url).path.split("/") if p]
        branch = get_github_default_branch(owner, repo)
        tree = github_tree(owner, repo, branch)
        candidate_paths = []
        for obj in tree:
            path = obj.get("path", "")
            # focus on plausible paths
            if not path.lower().endswith((".lua", ".vim")):
                continue
            if any(
                seg in path.lower()
                for seg in (
                    "lua/",
                    "colors/",
                    "themes/",
                    "theme/",
                    "highlight",
                    "palette",
                )
            ):
                candidate_paths.append(path)
        # fallback: if we found nothing filtered, take all .lua files
        if not candidate_paths:
            candidate_paths = [
                obj["path"]
                for obj in tree
                if obj.get("path", "").lower().endswith(".lua")
            ]
        # fetch and concatenate text
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
        # generic URL: just try to pull text and parse hexes
        texts.append(fetch_text(nvim_url))

    hexes = set()
    for t in texts:
        hexes.update(HEX_RE.findall(t))
        # catch 0xRRGGBB style
        for m in re.findall(r"0x([0-9A-Fa-f]{6})", t):
            hexes.add("#" + m)

    colors = []
    for h in hexes:
        rgb = hex_to_rgb(h)
        if rgb:
            colors.append(rgb)
    colors = list(dict.fromkeys(colors))
    if not colors:
        raise RuntimeError("No colors parsed from Neovim theme.")
    return colors


def avg_nearest_neighbor_distance(p1, p2):
    # average over p1 of the minimum sRGB distance to p2
    total = 0.0
    for c in p1:
        total += min(srgb_euclid(c, d) for d in p2)
    return total / max(1, len(p1))


def compare_palettes(iterm_url, nvim_url):
    iterm = load_iterm_colors(iterm_url)
    nvim = load_nvim_colors(nvim_url)

    # symmetric average (so order doesn’t matter)
    d1 = avg_nearest_neighbor_distance(iterm, nvim)
    d2 = avg_nearest_neighbor_distance(nvim, iterm)
    score = (d1 + d2) / 2.0

    return {
        "iterm_colors_count": len(iterm),
        "nvim_colors_count": len(nvim),
        "similarity_score": score,  # lower = more similar
    }


def main():
    ap = argparse.ArgumentParser(
        description="Compare iTerm .itermcolors vs Neovim theme colors."
    )
    ap.add_argument("--iterm", required=True, help="URL to .itermcolors file")
    ap.add_argument(
        "--nvim", required=True, help="URL to Neovim theme (repo URL or raw file URL)"
    )
    args = ap.parse_args()

    res = compare_palettes(args.iterm, args.nvim)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
