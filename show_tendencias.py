"""show_tendencias.py

Genera un HTML con las tendencias por sector y lo abre en el navegador.
- Lee `data/tendencias_inversion_por_sector.csv`
- Agrupa por `SECTOR` y pinta las cabeceras de sección según una paleta de colores (aprox. la del PNG adjunta)

Uso:
    python show_tendencias.py

Requisitos: pandas (ya listado en requirements.txt)
"""

from pathlib import Path
import pandas as pd
import webbrowser
import os
import unicodedata

# Paleta aproximada (extraída visualmente del PNG proporcionado)
PALETTE = [
    "#EDDCCF",  # beige
    "#C9D6C5",  # verde suave
    "#EDEFF1",  # gris claro
    "#F7EDE6",  # melocotón muy claro
    "#CBB0A0",  # marrón claro
]

# Optional mapping from exact sector name to a prefix. Edit if you want specific prefixes
# e.g. "Agricultura": "agr", "Automoción": "aut"
PREFIX_MAP = {
    # "Some Sector": "agr",
}


def make_prefix(sector: str) -> str:
    """Normalize a sector name to a short 3-letter prefix (lowercase, no accents)."""
    s = unicodedata.normalize("NFKD", sector)
    s = "".join(c for c in s if c.isalnum())
    s = s.lower()
    return s[:3] if len(s) >= 3 else s

CSV_PATH = Path(__file__).parent / "data" / "tendencias_inversion_por_sector.csv"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_HTML = OUTPUT_DIR / "tendencias_por_sector.html"


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
    sector_color = {s: palette[i % len(palette)] for i, s in enumerate(sectors)}

    html_parts = []
    html_parts.append(
        """
        <!doctype html>
        <html lang="es">
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Tendencias por sector</title>
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
        <h1>Tendencias por sector</h1>
        <table>
          <colgroup>
            <col style="width:8%">
            <col style="width:92%">
          </colgroup>
          <thead>
            <tr>
              <th>ID</th>
              <th>Tendencia</th>
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
        # Sector header
        html_parts.append(
            f"<tr class=\"sector-header\" style=\"background:{color};color:{txt_color};\"><td colspan=\"2\">{sector} <span class=\"sector-count\">({count})</span></td></tr>"
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
    """)

    return "\n".join(html_parts)


def main():
    if not CSV_PATH.exists():
        print(f"No se encuentra el CSV en: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    html = build_html(df, PALETTE)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"HTML generado en: {OUTPUT_HTML}")
    webbrowser.open(OUTPUT_HTML.resolve().as_uri())


if __name__ == "__main__":
    main()
