# Reflexivity - Investment Theme Explorer

Análisis automatizado de tendencias de inversión basado en evidencia de documentos SEC (10-K, 10-Q).

---

## 🚀 Instalación Rápida

### 1. Clonar repositorio
```bash
git clone https://github.com/ferranfont/reflexivity.git
cd reflexivity
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

**Nota**: La instalación incluye BART (~110MB) para generación de títulos con IA.

### 3. Configurar MySQL
Asegúrate de tener MySQL corriendo en `localhost:3306` con:
- Usuario: `root`
- Password: `Plus7070`
- Base de datos: `reflexivity`

---

## 📊 Uso Principal

### 1. Cargar datos de empresas
```bash
python mysql_scripts/upload_companies.py
python mysql_scripts/upload_evidence.py
python mysql_scripts/upload_ranks.py
```

### 2. Actualizar tabla `evidence` con sources y fechas
```bash
python mysql_scripts/update_evidence_sources.py
```

### 3. Generar títulos con BART (opcional, ~6-10 horas)
```bash
python mysql_scripts/add_evidence_titles.py
```

### 4. Descargar precios de acciones
```bash
# Una acción
python download_and_update_data_single_stock.py AAPL

# Todas las acciones (toma ~10 horas)
python download_and_update_data_all_stocks.py
```

### 5. Generar dashboard de empresa
```bash
python company_profile.py AAPL
```

---

## 📁 Estructura del Proyecto

```
reflexivity/
├── data/
│   ├── all_themes/          # CSVs de temas de inversión
│   └── trends_by_sector.csv
├── html/                     # Dashboards generados
├── mysql_scripts/            # Scripts de carga a MySQL
│   ├── upload_companies.py
│   ├── upload_evidence.py
│   ├── update_evidence_sources.py
│   └── add_evidence_titles.py
├── utils/
│   └── parse_filing_date.py # Parser de fechas de filings
├── company_profile.py        # Generador de dashboards
├── plot_chart.py             # Gráficos de precios
└── requirements.txt

```

---

## 🔧 Scripts Principales

| Script | Descripción | Tiempo estimado |
|--------|-------------|-----------------|
| `upload_companies.py` | Carga empresas únicas a MySQL | ~1 min |
| `update_evidence_sources.py` | Agrega sources y fechas | ~2 min |
| `add_evidence_titles.py` | Genera títulos con BART | ~6-10 horas |
| `download_and_update_data_all_stocks.py` | Descarga precios históricos | ~10 horas |
| `company_profile.py` | Genera dashboard HTML | ~5 seg |

---

## 📖 Documentación Adicional

- [BART Installation Guide](BART_INSTALLATION.md) - Guía detallada para generación de títulos con IA
- Ver carpeta `mysql_scripts/` para documentación de cada script

---

## 💡 Tips

- Los scripts en `mysql_scripts/` son seguros de ejecutar múltiples veces
- BART descarga modelo de 1.5GB solo la primera vez
- Usa `plot_chart.py` para gráficos standalone de cualquier símbolo
- Dashboard HTML es standalone (funciona sin servidor)

---

## 🤝 Contribuir

Haz forks, commits y pull requests al repositorio principal.
