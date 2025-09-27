import csv

import requests
from bs4 import BeautifulSoup

# Base URL for the GitHub repo tree
GITHUB_RAW = "https://raw.githubusercontent.com/mbadolato/iTerm2-Color-Schemes/master"
GITHUB_TREE = "https://api.github.com/repos/mbadolato/iTerm2-Color-Schemes/git/trees/master?recursive=1"


def fetch_all_schemes():
    resp = requests.get(GITHUB_TREE)
    resp.raise_for_status()
    data = resp.json()
    themes = []
    for obj in data.get("tree", []):
        path = obj.get("path", "")
        # We look for .itermcolors files under schemes/
        if path.startswith("schemes/") and path.endswith(".itermcolors"):
            name = path.split("/")[-1].replace(".itermcolors", "")
            url = f"{GITHUB_RAW}/{path}"
            themes.append((name, url))
    return themes


def save_csv(themes, filename="../data/interim/urls/iterm_themes.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "url"])
        for name, url in themes:
            writer.writerow([name, url])


if __name__ == "__main__":
    themes = fetch_all_schemes()
    print(f"Found {len(themes)} themes")
    save_csv(themes)
