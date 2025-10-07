from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
import os, uuid, json, threading, shlex, subprocess

# ---- Config (env or defaults) ----
K_MIN = int(os.getenv("K_MIN", "20"))
DATA_VIEW = os.getenv("DATA_VIEW", "/data/read_only")
WORK_DIR  = os.getenv("WORK_DIR", "/var/site_jobs")
SITE_NAME = os.getenv("SITE_NAME", "Site")
os.makedirs(WORK_DIR, exist_ok=True)

app = FastAPI(title="Model-to-Data Site Node")

# In-memory job store for demo; replace with Postgres in prod
JOBS: Dict[str, Dict] = {}

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/catalog/variables")
def catalog_variables():
    # Example metadata; customize to your site
    return {
        "template": "MNI152NLin2009bAsym",
        "resolution_mm": 2.0,
        "variables": [
            {"name":"dx","type":"category","levels":["PD","OCD","ET"]},
            {"name":"age","type":"number","bins":[0,10,20,30,40,50,60,70,80,90]},
            {"name":"sex","type":"category","levels":["M","F"]},
            {"name":"UPDRS_change","type":"number"},
            {"name":"YBOCS_change","type":"number"}
        ],
        "outcomes": [
            {"name":"UPDRS_change","N": 132},
            {"name":"YBOCS_change","N": 58}
        ]
    }

@app.post("/jobs")
async def submit_job(
    task: str = Form(...),
    outcome: str = Form(...),
    stat: str = Form("pearson"),
    mask: str = Form(""),
    filters: str = Form("{}"),
    map_file: UploadFile = File(...)
):
    if task != "map_to_outcome_v1":
        raise HTTPException(400, "Unsupported task")
    try:
        filters_dict = json.loads(filters) if filters else {}
        if not isinstance(filters_dict, dict):
            raise ValueError("filters must be a JSON object")
    except Exception as e:
        raise HTTPException(400, f"Invalid filters JSON: {e}")

    job_id = str(uuid.uuid4())
    job_dir = os.path.join(WORK_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    map_path = os.path.join(job_dir, "map.nii.gz")
    with open(map_path, "wb") as f:
        f.write(await map_file.read())

    JOBS[job_id] = {"status":"queued","result":None,"n": None}

    t = threading.Thread(
        target=_run_job,
        args=(job_id, map_path, outcome, stat, mask, filters_dict),
        daemon=True
    )
    t.start()
    return {"job_id": job_id}

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    j = JOBS.get(job_id)
    if not j:
        raise HTTPException(404, "Not found")
    if j["status"] != "done":
        return {"status": j["status"]}
    # privacy gate
    if (j["n"] or 0) < K_MIN:
        return {"status":"blocked", "reason": f"n<{K_MIN}"}
    return {"status":"done", **j["result"]}

def _run_job(job_id: str, map_path: str, outcome: str, stat: str, mask: str, filters_dict: Dict):
    try:
        JOBS[job_id]["status"]="running"
        out_json = os.path.join(WORK_DIR, job_id, "result.json")

        # Sandbox worker: no network; read-only data mount
        cmd = f"""
        docker run --rm --network=none \
          -v {shlex.quote(DATA_VIEW)}:/data:ro \
          -v {shlex.quote(os.path.dirname(map_path))}:/work \
          -e DATA_DIR=/data \
          -e MAP_PATH=/work/map.nii.gz \
          -e OUT_JSON=/work/result.json \
          -e OUTCOME={shlex.quote(outcome)} \
          -e MASK_NAME={shlex.quote(mask)} \
          -e STAT={shlex.quote(stat)} \
          -e FILTERS={shlex.quote(json.dumps(filters_dict))} \
          map-runner:latest
        """
        subprocess.check_call(cmd, shell=True)

        with open(out_json) as f:
            res = json.load(f)

        n = int(res.get("n",0))
        # round/cap precision
        result = {
            "site": SITE_NAME,
            "n": n,
            "R": round(float(res.get("R",0)), 3) if res.get("R") is not None else None,
            "p": round(float(res.get("p",1.0)), 3) if res.get("p") is not None else None,
            "outcome": outcome
        }
        JOBS[job_id]["n"] = n
        JOBS[job_id]["result"] = result
        JOBS[job_id]["status"]="done"
    except Exception as e:
        JOBS[job_id]["status"]="error"
        JOBS[job_id]["result"]={"error": str(e)}
