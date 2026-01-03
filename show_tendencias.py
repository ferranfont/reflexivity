# -*- coding: utf-8 -*-
"""show_trends.py

Generates an HTML with trends grouped by sector and opens it in the browser.
- Reads `data/tendencias_inversion_por_sector.csv`
- Groups by `SECTOR`, assigns header colors and generates a cleaned CSV `data/trends_by_sector.csv`.

Usage:
    python show_trends.py

Requirements: pandas
"""

from pathlib import Path
import pandas as pd
import webbrowser
import unicodedata

# Palette imported from central config
from config import PALETTE, EXPANDED_PALETTE
# use expanded palette to color sector headers with more variety
PALETTE_TO_USE = EXPANDED_PALETTE

# Optional mapping from exact sector name to a prefix. Edit if you want specific prefixes
# e.g. "Agricultura": "agr", "Automoción": "aut"
PREFIX_MAP = {
    # "Some Sector": "agr",
}

# Mapping from Spanish sector names to English display names used in headers
SECTOR_TRANSLATIONS = {
    "Tecnología": "Technology",
    "Energía y Utilities": "Energy and Utilities",
    "Financiero": "Financials",
    "Salud": "Health",
    "Industrial": "Industrial",
    "Consumo y Retail": "Consumer and Retail",
    "Inmobiliario": "Real Estate",
    "Materiales y Minería": "Materials and Mining",
    "Transporte y Logística": "Transportation and Logistics",
    "Automotive": "Automotive",
    "Automotriz": "Automotive",
    "Entretenimiento y Medios": "Entertainment and Media",
    "Agricultura": "Agriculture",
    "Defensa y Aeroespacial": "Defense and Aerospace",
    "Telecomunicaciones": "Telecommunications",
    "Hospitalidad": "Hospitality",
    "Servicios Profesionales": "Professional Services",
    "Otros": "Other",
}


def make_prefix(sector: str) -> str:
    """Normalize a sector name to a short 3-letter prefix (lowercase, no accents)."""
    s = unicodedata.normalize("NFKD", sector)
    s = "".join(c for c in s if c.isalnum())
    s = s.lower()
    return s[:3] if len(s) >= 3 else s


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def text_color_for_bg(hex_color: str):
    r, g, b = hex_to_rgb(hex_color)
    # Perceived luminance
    lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#000" if lum > 0.6 else "#fff"


def build_html(df: pd.DataFrame, palette: list):
    sectors = sorted(df["SECTOR"].unique())
    # Prefer the expanded palette for better color variety
    color_source = PALETTE_TO_USE if 'PALETTE_TO_USE' in globals() else palette
    sector_color = {s: color_source[i % len(color_source)] for i, s in enumerate(sectors)}

    html_parts = []
    html_parts.append(
        """
        <!doctype html>
        <html lang="en">
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Trends</title>
        <style>
          body { font-family: Arial, Helvetica, sans-serif; margin: 20px; }
          .container { max-width: 900px; margin: 0 auto; }
          table { border-collapse: collapse; width: 100%; }
          th, td { padding: 8px 10px; border: 1px solid #ddd; }
          tr.sector-header td { font-weight: bold; font-size: 1.05rem; }
          tr.item-row:nth-child(even) { background: #fbfbfb; }
          .sector-count { font-size: 0.9rem; opacity: 0.9; margin-left: 8px; }
        </style>
        </head>
        <body>
        <div class="container">
        <h1>Trends</h1>
        <table>
          <colgroup>
            <col style="width:12%">
            <col style="width:88%">
          </colgroup>
          <thead>
            <tr>
              <th>ID</th>
              <th>Trend</th>
            </tr>
          </thead>
          <tbody>
        """
    )

    # For each sector, add a sector header row (full-width via colspan) and then rows
    for sector in sectors:
        color = sector_color[sector]
        txt_color = text_color_for_bg(color)
        sector_rows = df[df["SECTOR"] == sector]
        count = len(sector_rows)
        # determine prefix (configurable via PREFIX_MAP, else auto-generate)
        prefix = PREFIX_MAP.get(sector, make_prefix(sector))
        # Sector header (use English display name if available)
        display_name = SECTOR_TRANSLATIONS.get(sector, sector)
        html_parts.append(
            f"<tr class=\"sector-header\" style=\"background:{color};color:{txt_color};\"><td colspan=\"2\">{display_name} <span class=\"sector-count\">({count})</span></td></tr>"
        )
        for idx, (_, row) in enumerate(sector_rows.iterrows(), start=1):
            # escape HTML minimally
            trend = str(row.get("TENDENCIA", "")).replace("&", "&amp;").replace("<", "&lt;")
            id_str = f"{prefix}{idx}"
            html_parts.append(
                f"<tr class=\"item-row\"><td>{id_str}</td><td>{trend}</td></tr>"
            )

    html_parts.append("""
      </tbody>
    </table>
    </div>
    </body>
    </html>
    """
    )

    return "\n".join(html_parts)


# Paths
CSV_PATH = Path(__file__).parent / "data" / "tendencias_inversion_por_sector.csv"
DATA_TRENDS = Path(__file__).parent / "data" / "trends_by_sector.csv"
HTML_DIR = Path(__file__).parent / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_HTML = HTML_DIR / "trends_by_sector.html"


def main():
    if not CSV_PATH.exists():
        print(f"No se encuentra el CSV en: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)

    # Build cleaned CSV with per-sector prefixed IDs and English sector names
    rows = []
    for sector in sorted(df["SECTOR"].unique()):
        prefix = PREFIX_MAP.get(sector, make_prefix(sector))
        sector_rows = df[df["SECTOR"] == sector]
        for idx, (_, row) in enumerate(sector_rows.iterrows(), start=1):
            id_str = f"{prefix}{idx}"
            trend = row.get("TENDENCIA", "")
            display_sector = SECTOR_TRANSLATIONS.get(sector, sector)
            rows.append({"id": id_str, "sector": display_sector, "trend": trend, "original_id": row.get("ID")})

    df_clean = pd.DataFrame(rows)
    df_clean.to_csv(DATA_TRENDS, index=False, encoding="utf-8")
    print(f"Clean CSV written to: {DATA_TRENDS}")

    # Generate and write HTML to the html/ directory
    html = build_html(df, PALETTE)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML generado en: {OUTPUT_HTML}")
    webbrowser.open(OUTPUT_HTML.resolve().as_uri())


if __name__ == "__main__":
    main()
