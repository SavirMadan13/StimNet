# Site Node Starter (No Broker)
A minimal, production-leaning scaffold for a **model-to-data** site node. Requesters POST a connectivity map (NIfTI) and get back **aggregate stats only** (n, R, p). No patient-level data leaves the institution.

## What’s inside
```
site-node-starter/
├─ README.md
├─ requirements.txt
├─ docker-compose.yml              # optional helper to run uvicorn + nginx
├─ .env.example                    # environment overrides
├─ site_app/
│  └─ main.py                      # FastAPI: /healthz, /catalog/variables, /jobs, /jobs/{id}
├─ worker/
│  ├─ Dockerfile                   # sandboxed analysis image
│  └─ run_job.py                   # map × subject connectivity → score → R vs outcome
├─ nginx/
│  └─ site.conf                    # reverse proxy + TLS (and optional mTLS)
├─ data/
│  └─ read_only/                   # curated, de-identified views (mounted read-only)
│     ├─ subjects.csv              # subject_id, dx, age, sex, visit, ...
│     ├─ outcomes.csv              # subject_id, visit, outcomes...
│     ├─ paths.csv                 # subject_id, visit, conn_path (absolute path to subj NIfTI on this machine)
│     └─ masks/                    # optional ROI masks (e.g., STN.nii.gz)
└─ var/
   └─ site_jobs/                   # temp workspace for uploads/results
```

## Quick start (local demo)
1) **Python deps**
```
pip install -r requirements.txt
```
2) **Build the worker image**
```
cd worker
docker build -t map-runner:latest .
```
3) **Run the FastAPI app (dev)**
```
uvicorn site_app.main:app --host 127.0.0.1 --port 8000
```
4) **(Optional) Run Nginx reverse proxy**  
Populate TLS certs (self-signed is fine for local), then:
```
docker compose up -d nginx
```
or use your host Nginx with `nginx/site.conf`.

## Endpoints
- `GET /healthz` → liveness
- `GET /catalog/variables` → safe metadata (template, variables, outcomes, N)
- `POST /jobs` (multipart) → upload `map_file` and fields: `task`, `outcome`, `stat`, `mask`, `filters`
- `GET /jobs/{id}` → status or `{n, R, p}` (blocked if n < K_MIN)

### Example (submit job)
```
curl -k -X POST https://localhost/jobs   -F 'map_file=@/absolute/path/to/map.nii.gz'   -F 'task=map_to_outcome_v1'   -F 'outcome=UPDRS_change'   -F 'stat=pearson'   -F 'mask=STN'   -F 'filters={"dx":"PD","visit":"6mo"}'
```

### Poll
```
curl -k https://localhost/jobs/<JOB_ID>
```

> Use `-k` to allow self-signed TLS locally. For real deployments, use proper certs (Let’s Encrypt) and consider **mTLS** (client certs).

## Data view expectations
Place **de-identified** site-controlled views here: `data/read_only/`
- `subjects.csv`: columns `subject_id, visit, dx, age, sex, ...`
- `outcomes.csv`: columns `subject_id, visit, UPDRS_change, YBOCS_change, ...`
- `paths.csv`: columns `subject_id, visit, conn_path` (absolute path to per-subject NIfTI, all in same template as map)
- `masks/*.nii.gz`: optional ROI masks (e.g., `STN.nii.gz`).

## Privacy guardrails
- Minimum cohort size `K_MIN` enforced before returning results.
- Worker container runs with `--network=none` and `/data:ro` mounts.
- Outputs rounded to 3 decimals; you can add DP noise if desired.

## Production notes
- Put uvicorn behind Nginx (TLS/mTLS), enable rate limiting & access logs.
- Replace the thread runner with a queue (Redis/RQ or Celery) for scale.
- Store jobs/results in Postgres instead of in-memory dict.
- Verify allowlisted images (e.g., cosign) before `docker run`.
- Lock Docker down with seccomp/apparmor profiles and CPU/mem limits.
