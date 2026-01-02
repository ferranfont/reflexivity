# -*- coding: utf-8 -*-
"""show_count_pie.py

Generates a pie chart with the number of trends per sector, saves an SVG and an HTML
file under the project's `html/` folder and opens the HTML in the default browser.

Usage:
    python show_count_pie.py

Requirements: pandas, matplotlib (already in requirements.txt)
"""

from pathlib import Path
import pandas as pd
import webbrowser
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from config import PALETTE, EXPANDED_PALETTE

# Paths
ROOT = Path(__file__).parent
DATA_TRENDS = ROOT / "data" / "trends_by_sector.csv"
CSV_RAW = ROOT / "data" / "tendencias_inversion_por_sector.csv"
HTML_DIR = ROOT / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)
SVG_PATH = HTML_DIR / "sector_counts.svg"
OUTPUT_HTML = HTML_DIR / "sector_counts_pie.html"


def read_sector_counts():
    if DATA_TRENDS.exists():
        df = pd.read_csv(DATA_TRENDS, encoding="utf-8")
        if "sector" in df.columns:
            counts = df["sector"].value_counts()
            return counts.sort_values(ascending=False)
    # fallback: compute from raw CSV and use SECTOR column
    if CSV_RAW.exists():
        df = pd.read_csv(CSV_RAW)
        counts = df["SECTOR"].value_counts()
        return counts.sort_values(ascending=False)
    raise FileNotFoundError("No input CSV found (data/trends_by_sector.csv or data/tendencias_inversion_por_sector.csv)")


def build_pie(counts, svg_path: Path):
    labels = counts.index.tolist()
    sizes = counts.values

    # If too many sectors, limit label size font
    fig, ax = plt.subplots(figsize=(10, 10))
    # Use expanded palette to reduce repeated colors
    colors = [EXPANDED_PALETTE[i % len(EXPANDED_PALETTE)] for i in range(len(sizes))]

    # autopct function that shows percent and absolute count
    def make_autopct(sizes):
        total = sum(sizes)
        def inner(pct):
            # round to nearest integer for count
            val = int(round(pct * total / 100.0))
            return f"{pct:.1f}%\n({val})"
        return inner

    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct=make_autopct(sizes),
        startangle=140,
        textprops={"fontsize": 8},
    )
    ax.axis("equal")
    plt.title("Trends count by sector")

    # Save SVG for embedding
    fig.savefig(svg_path, format="svg", bbox_inches="tight")
    plt.close(fig)


def write_html_with_svg(svg_path: Path, out_html: Path):
    svg_content = svg_path.read_text(encoding="utf-8")
    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Sector distribution (pie)</title>
      <style>
        body {{ font-family: Arial, Helvetica, sans-serif; margin: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; text-align: center; }}
        .legend {{ font-size: 0.9rem; margin-top: 12px; text-align: left; display: inline-block; }}
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Trends by Sector (count)</h1>
        {svg_content}
      </div>
    </body>
    </html>
    """
    out_html.write_text(html, encoding="utf-8")


def main():
    counts = read_sector_counts()
    if counts.sum() == 0:
        print("No data to plot")
        return

    build_pie(counts, SVG_PATH)
    write_html_with_svg(SVG_PATH, OUTPUT_HTML)
    print(f"SVG saved to: {SVG_PATH}")
    print(f"HTML saved to: {OUTPUT_HTML}")
    webbrowser.open(OUTPUT_HTML.resolve().as_uri())


if __name__ == "__main__":
    main()
