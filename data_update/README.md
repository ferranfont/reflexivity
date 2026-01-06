# Herramientas de Actualización y Mantenimiento

Esta carpeta contiene scripts esenciales para mantener actualizados los datos del sistema.

## 🚀 Script Principal
**`../update_system_main.py`** (En la raíz del proyecto)  
Este es el único script que necesitas ejecutar rutinariamente. Orquesta todo el proceso:
1. Descarga precios de mercado (incrementalmente).
2. Regenera perfiles HTML.
3. Regenera páginas de temas.

---

## 🛠️ Scripts Individuales (Uso Avanzado)

Si necesitas ejecutar tareas específicas, puedes usar estos scripts directamente:

- **`download_and_update_data_all_stocks.py`**: 
  - Descarga masiva de precios históricos para TODAS las acciones.
  - Es incremental: si ya hay datos, solo baja lo nuevo.

- **`download_and_update_data_single_stock.py`**:
  - Uso: `python download_and_update_data_single_stock.py AAPL --upload`
  - Actualiza una sola acción rápidamente.

- **`download_logos.py`**:
  - Descarga logos faltantes usando la API de Logo.dev.

- **`regenerate_all_profiles.py`**:
  - Borra y vuelve a crear todos los archivos `*_profile.html` en la carpeta `html/`.
  - Útil si cambiaste el diseño o la lógica de visualización.

- **`regenerate_all_themes.py`**:
  - Vuelve a crear todas las páginas `*_detail.html` de los temas de inversión.

- **`classify_themes.py`** y **`fetch_all_themes.py`**:
  - Scripts legacy o de utilidad para la clasificación inicial de temas.
