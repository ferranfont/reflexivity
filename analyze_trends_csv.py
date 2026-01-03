import pandas as pd
from pathlib import Path
import re

p = Path('data/trends_by_sector.csv')
if not p.exists():
    print('MISSING')
    raise SystemExit(1)

df = pd.read_csv(p)
print('ROWS:', len(df))
print('COLUMNS:', list(df.columns))
print('\nSample:')
print(df.head().to_string(index=False))

# Missing values
print('\nMissing per column:')
print(df.isna().sum())

# ID format: prefix letters then digits
pattern = re.compile(r'^[a-z]{1,}[0-9]+$')
df['id_ok'] = df['id'].astype(str).str.match(pattern)
print('\nIDs that do not match prefix+number pattern:', (~df['id_ok']).sum())
if (~df['id_ok']).any():
    print(df.loc[~df['id_ok'], ['id']].head().to_string(index=False))

# Duplicate ids
dups = df['id'].duplicated().sum()
print('\nDuplicate id count:', dups)
if dups:
    print(df[df['id'].duplicated(keep=False)].sort_values('id').to_string(index=False))

# Duplicate rows fully
dup_rows = df.duplicated().sum()
print('\nExact duplicate rows:', dup_rows)

# Sectors list and counts
print('\nTop sectors (by count):')
print(df['sector'].value_counts().head(20).to_string())

# any trends missing names
missing_trends = df['trend'].isna().sum()
print('\nMissing trend names:', missing_trends)

print('\nAll good checks:')
all_ok = (df['id_ok'].all() and dups==0 and dup_rows==0 and missing_trends==0)
print(all_ok)
