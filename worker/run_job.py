import os, json, numpy as np, nibabel as nib
from scipy import stats
import pandas as pd

DATA_DIR  = os.environ["DATA_DIR"]
MAP_PATH  = os.environ["MAP_PATH"]
OUT_JSON  = os.environ.get("OUT_JSON","/work/result.json")
OUTCOME   = os.environ["OUTCOME"]
MASK_NAME = os.environ.get("MASK_NAME","")
STAT      = os.environ.get("STAT","pearson")
FILTERS   = json.loads(os.environ.get("FILTERS","{}"))

# Load requester-provided map
m_img = nib.load(MAP_PATH); m = m_img.get_fdata().astype(np.float32)

# Load site-controlled read-only tables
subs_path  = os.path.join(DATA_DIR, "subjects.csv")
outc_path  = os.path.join(DATA_DIR, "outcomes.csv")
paths_path = os.path.join(DATA_DIR, "paths.csv")

subs = pd.read_csv(subs_path)
outc = pd.read_csv(outc_path)
paths = pd.read_csv(paths_path)

# Apply safe filters
df = subs.copy()
for k, v in FILTERS.items():
    if k in df.columns:
        df = df[df[k] == v]

# Join outcomes and connectivity paths
df = df.merge(outc, on=["subject_id","visit"], how="inner")
df = df.merge(paths, on=["subject_id","visit"], how="inner")

# Optional mask
mask = None
if MASK_NAME:
    mask_path = os.path.join(DATA_DIR, "masks", f"{MASK_NAME}.nii.gz")
    if os.path.exists(mask_path):
        mask = nib.load(mask_path).get_fdata().astype(bool)

scores = []
ys = []

for _, row in df.iterrows():
    conn_img = nib.load(row["conn_path"])
    c = conn_img.get_fdata().astype(np.float32)

    # NOTE: Assumes same grid as map; in production, resample deterministically.
    x = c
    if mask is not None:
        x = x * mask

    valid = np.isfinite(x) & np.isfinite(m)
    if not valid.any():
        continue

    s = float((x[valid] * m[valid]).sum())
    scores.append(s)
    ys.append(float(row[OUTCOME]))

scores = np.array(scores, dtype=np.float64)
ys     = np.array(ys, dtype=np.float64)
n = int(len(scores))

result = {"n": n, "R": None, "p": None}

if n >= 3 and np.std(scores) > 0 and np.std(ys) > 0:
    if STAT.lower() == "spearman":
        R, p = stats.spearmanr(scores, ys)
    else:
        R, p = stats.pearsonr(scores, ys)
    result.update({"R": float(R), "p": float(p)})

with open(OUT_JSON, "w") as f:
    json.dump(result, f)
