# BART Installation Guide for Evidence Titles

## What is BART?
BART (Bidirectional and Auto-Regressive Transformers) is Facebook's state-of-the-art AI model for text summarization. It generates **natural, concise titles** instead of just copying sentences.

---

## Installation Steps

### Step 1: Install Dependencies
```bash
pip install transformers torch sentencepiece
```

**Note**: This will download ~2GB of packages (PyTorch + Transformers)

---

### Step 2: Run the Script
```bash
cd D:\PYTHON\ALGOS\reflexivity
python mysql_scripts\add_evidence_titles.py
```

**What happens:**
1. **First run only**: Downloads BART model (~1.5GB) to cache folder
   - Location: `C:\Users\YourUser\.cache\huggingface\hub\`
   - **This is a one-time download**

2. Processes all 11,949 evidence entries
3. Generates high-quality titles using AI
4. Updates MySQL `evidence` table with `head_title` column

---

## Performance Estimates

| Metric | Value |
|--------|-------|
| **Download time** (first run) | ~10-15 minutes |
| **Model size** | 1.5 GB |
| **Processing speed** | ~2-3 seconds per evidence |
| **Total time** | ~6-10 hours for 11,949 entries |
| **CPU usage** | High (100% on one core) |
| **RAM usage** | ~2-3 GB |

---

## Optimization Tips

### Use GPU (if available)
Edit line 40 in `add_evidence_titles.py`:
```python
device=-1  # CPU
# Change to:
device=0   # GPU (10x faster!)
```

### Run overnight
The script is safe to run in the background. It saves progress in batches of 100.

---

## Fallback: Use SUMY instead

If BART is too slow or you don't want to download 1.5GB:

1. **Install SUMY**:
```bash
pip install sumy nltk
python -m nltk.downloader punkt stopwords
```

2. **Modify script** (contact for details)
   - SUMY is ~100x faster
   - Lower quality (extractive, not generative)
   - No model download needed

---

## Example Output

### Input (Evidence):
```
El compromiso de Apple con la Inteligencia Artificial es evidente a través de
su integración en dispositivos y plataformas, destacado por la introducción de
'Apple Intelligence', un sistema de inteligencia personal que aprovecha modelos
generativos...
```

### BART Output (Title):
```
Apple integra IA en dispositivos con sistema Apple Intelligence
```

### SUMY Output (for comparison):
```
El compromiso de Apple con la Inteligencia Artificial es evidente a través de
su integración en dispositivos y plataformas
```

---

## Troubleshooting

### Error: "No module named 'transformers'"
```bash
pip install transformers
```

### Error: "Slow download or timeout"
- Check internet connection
- Download may take 10-15 minutes (1.5GB)
- Script will resume if interrupted

### Script too slow?
- Use GPU (change `device=-1` to `device=0`)
- Or switch to SUMY (faster, lower quality)

---

## After Completion

Once titles are generated, regenerate the company dashboard:
```bash
python company_profile.py AAPL
```

You'll see:
```
Evidence #1 (Q4 2024) - Apple integra IA en dispositivos con Apple Intelligence
```

---

**Questions?** Contact the development team.
