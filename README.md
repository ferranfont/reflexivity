# Reflexivity - Investment Theme Explorer

Análisis automatizado de tendencias de inversión basado en evidencia de documentos SEC (10-K, 10-Q), visualizado a través de un dashboard web dinámico.

---

## 🚀 Instalación Rápida con Git

### 1. Clonar el repositorio
Si aún no tienes el código en tu máquina:
```bash
git clone https://github.com/ferranfont/reflexivity.git
cd reflexivity
```

### 2. Preparar el entorno
Se recomienda usar un entorno virtual (opcional pero recomendado):
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 3. Instalar librerías
Instala todas las dependencias necesarias definidas en `requirements.txt`:
```bash
pip install -r requirements.txt
```
*Nota: Esto instalará librerías de análisis de datos (pandas, numpy), visualización (plotly), servidor web y modelos de IA (transformers) para el procesamiento de texto.*

---

## 🏗️ Cómo Usar el Sistema

El sistema funciona con un servidor local que genera los análisis bajo demanda.

### 1. Iniciar la Aplicación
Simplemente ejecuta el script principal. Esto iniciará el servidor web y abrirá el dashboard en tu navegador (http://localhost:8000).
```bash
python show_main.py
```

### 2. Navegación
- **Main Trends**: Vista general de todos los temas de inversión.
- **Industry Explorer**: Explorador detallado por industrias.
- **Perfiles de Empresa**: Haz clic en cualquier ticker (ej: NVDA, AAPL) para generar un análisis profundo en tiempo real.
- **Temas**: Haz clic en cualquier tema para ver el desglose de empresas y métricas asociadas.

---

## 🔄 MANTENIMIENTO Y ACTUALIZACIÓN DEL SISTEMA
Para mantener los datos frescos (precios de acciones, métricas) y actualizar el sitio web con la última información:

**EJECUTA SOLAMENTE ESTE COMANDO:**
```bash
python update_system_main.py
```
Este script maestro se encarga automáticamente de:
1.  **Descargar nuevos datos de mercado** (solo lo nuevo desde la última vez).
2.  **Actualizar base de datos MySQL**.
3.  **Regenerar todos los perfiles HTML** de empresas.
4.  **Regenerar todas las páginas HTML** de temas de inversión.

---

## 🛠️ Herramientas Individuales (Carpeta `data_update/`)

Si solo necesitas realizar una tarea específica (no recomendado para uso general):

### Descarga de Precios
```bash
# Para una sola acción (rápido):
python data_update/download_and_update_data_single_stock.py NVDA --upload

# Para TODAS las acciones (tarda varias horas):
python data_update/download_and_update_data_all_stocks.py
```

### Logos e Imágenes
```bash
# Descargar logos de empresas faltantes:
python data_update/download_logos.py
```

### Regeneración Masiva (Caché)
Si cambias el diseño y quieres actualizar todas las páginas generadas anteriormente:
```bash
python data_update/regenerate_all_profiles.py
python data_update/regenerate_all_themes.py
```

---

## 📁 Estructura del Código

```
reflexivity/
├── show_main.py              # 🚀 PUNTO DE ENTRADA: Inicia la app y el servidor
├── reflexivity_server.py     # Servidor web inteligente (maneja rutas y generación dinámica)
├── show_trends.py            # Genera la página principal de tendencias
├── show_company_profile.py   # Genera el análisis detallado de una empresa
├── show_theme.py             # Genera el análisis de un tema de inversión específicos
│
├── data_update/              # 🛠️ Herramientas de Mantenimiento
│   ├── download_*.py         # Scripts para bajar precios y logos
│   └── regenerate_*.py       # Scripts para actualizar caché masivamente
│
├── mysql_scripts/            # Scripts de base de datos (ETL, carga inicial)
├── html/                     # Carpeta donde se guardan los reportes generados (.html)
└── data/                     # Archivos de datos estáticos (CSVs, configuraciones)
```

## ⚙️ Configuración
El sistema utiliza un archivo `.env` en la raíz para las credenciales de base de datos MySQL y claves de API (como Logo.dev). Asegúrate de tenerlo configurado correctamente.
