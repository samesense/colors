import argparse
import csv
import time
from urllib.parse import urlparse

import requests


def is_github_repo_url(url):
    """Check if the URL looks like github.com/owner/repo"""
    u = urlparse(url)
    parts = [p for p in u.path.split("/") if p]
    return u.netloc == "github.com" and len(parts) == 2


def repo_has_theme_files(owner, repo):
    """Check GitHub repo tree for .lua or .vim files likely containing theme colors."""
    try:
        api = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        r = requests.get(api, timeout=20)
        if r.status_code != 200:
            return False, f"API error {r.status_code}"
        tree = r.json().get("tree", [])
        for obj in tree:
            path = obj.get("path", "").lower()
            if path.endswith((".lua", ".vim")) and any(
                seg in path for seg in ("color", "theme", "palette")
            ):
                return True, "theme file found"
        return False, "no theme files"
    except Exception as e:
        return False, f"error: {e}"


def main():
    ap = argparse.ArgumentParser(
        description="Check Neovim theme URLs for compatibility"
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
                results.append((name, url, "invalid_repo_url"))
                print(f"{name}: {url} -> invalid_repo_url")
                continue

            owner, repo = [p for p in urlparse(url).path.split("/") if p]
            ok, reason = repo_has_theme_files(owner, repo)
            status = "compatible" if ok else f"incompatible ({reason})"
            results.append((name, url, status))
            print(f"{name}: {url} -> {status}")
            time.sleep(0.5)

    # save results
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["name", "url", "status"])
        writer.writerows(results)


if __name__ == "__main__":
    main()
