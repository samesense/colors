import argparse
import re

import pandas as pd


def normalize_name(name):
    """Lowercase and strip punctuation for matching."""
    return re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()


def share_keyword(iterm, nvim):
    """Check if iTerm and Neovim names share a keyword (obvious hit)."""
    iterm_words = set(normalize_name(iterm).split())
    nvim_words = set(normalize_name(nvim).split())

    stopwords = {"nvim", "vim", "theme", "colors", "color", "dark", "light"}
    iterm_words -= stopwords
    nvim_words -= stopwords

    return (
        len(iterm_words & nvim_words) > 0
        or ("nord" in iterm.lower() and "nord" in nvim.lower())
        or ("gruvbox" in iterm.lower() and "gruvbox" in nvim.lower())
    )


def main():
    ap = argparse.ArgumentParser(
        description="Make Top 50 table of matches, excluding obvious hits and collapsing duplicates."
    )
    ap.add_argument(
        "--tsv", required=True, help="comparison_results.tsv with similarity_index_lab"
    )
    ap.add_argument(
        "--out", default="../data/end/top50_filtered.tsv", help="Output TSV file"
    )
    args = ap.parse_args()

    # Load data
    df = pd.read_csv(args.tsv, sep="\t")

    if "similarity_index_lab" not in df.columns:
        raise ValueError("TSV must contain a 'similarity_index_lab' column")

    # Collapse duplicates: keep max similarity per pair
    df = df.groupby(["iterm_name", "nvim_name"], as_index=False).agg(
        {"similarity_index_lab": "max"}
    )

    # Drop obvious matches
    mask = df.apply(
        lambda row: share_keyword(row["iterm_name"], row["nvim_name"]), axis=1
    )
    filtered = df[~mask].copy()

    crit = filtered.apply(
        lambda row: row["nvim_name"] in ("theme.nvim", "nvim"), axis=1
    )
    filtered = filtered[~crit]

    # Sort by similarity, take top 50
    top50 = filtered.sort_values("similarity_index_lab", ascending=False).head(50)

    # Save to TSV
    top50.to_csv(args.out, sep="\t", index=False)
    print(f"✅ Saved filtered Top 50 to {args.out}")

    # Print preview
    print(
        top50[["iterm_name", "nvim_name", "similarity_index_lab"]].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
