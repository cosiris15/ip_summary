from __future__ import annotations

import asyncio
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

ROOT = Path(__file__).parent.resolve()
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ip_summary.config import Settings, load_settings
from ip_summary.pipeline import aggregate_to_outputs, load_headers, process_contracts
from ip_summary.storage import load_intermediate_folder, aggregate_results
from ip_summary.tasks import Task, TaskManager

DEFAULT_CONFIG_PATH = Path("config/deepseek_config.yaml")
UPSTREAM_HEADERS_PATH = Path("表头字段/版权授权链-上游类-表头信息.xlsx")
DOWNSTREAM_HEADERS_PATH = Path("表头字段/版权授权链-下游类-表头信息.xlsx")
TASK_ROOT = Path("tasks")

app = FastAPI(title="IP合同梳理前端 API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

task_manager = TaskManager(TASK_ROOT)
headers_def = load_headers(UPSTREAM_HEADERS_PATH, DOWNSTREAM_HEADERS_PATH)


def _load_settings_for_task(task: Task) -> Settings:
    settings = load_settings(DEFAULT_CONFIG_PATH)
    pipeline = settings.pipeline.model_copy(
        update={
            "input_dir": task.input_dir,
            "intermediate_dir": task.intermediate_dir,
            "final_dir": task.final_dir,
        }
    )
    return Settings(llm=settings.llm, pipeline=pipeline)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tasks", response_model=Task)
def create_task(name: str, my_party: str):
    return task_manager.create_task(name=name, my_party=my_party)


@app.get("/tasks", response_model=List[Task])
def list_tasks():
    return task_manager.list_tasks()


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    try:
        return task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")


@app.post("/tasks/{task_id}/upload")
async def upload_files(task_id: str, files: List[UploadFile] = File(...)):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

    saved: List[str] = []
    for f in files:
        dest = Path(task.input_dir) / f.filename
        with dest.open("wb") as out:
            content = await f.read()
            out.write(content)
        saved.append(f.filename)
    return {"saved": saved, "input_dir": str(task.input_dir)}


@app.get("/tasks/{task_id}/files")
def list_uploaded_files(task_id: str):
    """List all uploaded files for a task."""
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

    input_dir = Path(task.input_dir)
    if not input_dir.exists():
        return {"files": [], "count": 0}

    files = []
    for f in sorted(input_dir.iterdir()):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "modified": f.stat().st_mtime,
            })
    return {"files": files, "count": len(files)}


@app.post("/tasks/{task_id}/run")
async def run_task(
    task_id: str,
    my_party: Optional[str] = None,
    concurrency: int = 3,
    force_direction: Optional[str] = None,
):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

    task_manager.update_status(task_id, "running", "LLM处理中")
    settings = _load_settings_for_task(task)
    pipeline = settings.pipeline.model_copy(update={"concurrent_requests": concurrency})
    settings = Settings(llm=settings.llm, pipeline=pipeline)

    async def _job():
        try:
            results = await process_contracts(
                settings=settings,
                my_party=my_party or task.my_party,
                upstream_header_path=UPSTREAM_HEADERS_PATH,
                downstream_header_path=DOWNSTREAM_HEADERS_PATH,
                force_direction=force_direction if force_direction in {"upstream", "downstream"} else None,
            )
            summary = {"upstream": 0, "downstream": 0}
            for r in results:
                summary[r.direction] += 1
            task_manager.update_summary(task_id, summary)
            task_manager.update_status(task_id, "completed", f"处理完成 {len(results)} 份合同")
        except Exception as exc:
            task_manager.update_status(task_id, "failed", str(exc))

    asyncio.create_task(_job())
    return {"status": "accepted", "message": "已进入后台处理"}


@app.get("/tasks/{task_id}/results")
def get_results(task_id: str, direction: str):
    if direction not in {"upstream", "downstream"}:
        raise HTTPException(status_code=400, detail="direction must be upstream or downstream")
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

    folder = Path(task.intermediate_dir) / direction
    results = load_intermediate_folder(folder, direction=direction) if folder.exists() else []
    # Only expose fields & metadata needed for editing.
    payload = []
    for r in results:
        payload.append(
            {
                "contract_path": str(r.contract_path),
                "direction": r.direction,
                "fields": r.fields,
                "classification": r.classification.model_dump(),
            }
        )
    return {"count": len(payload), "items": payload}


@app.patch("/tasks/{task_id}/results/{direction}/{filename}")
def update_result(task_id: str, direction: str, filename: str, fields: Dict[str, object]):
    if direction not in {"upstream", "downstream"}:
        raise HTTPException(status_code=400, detail="direction must be upstream or downstream")
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    target = Path(task.intermediate_dir) / direction / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="file not found")
    payload = json.loads(target.read_text(encoding="utf-8"))
    payload["fields"].update(fields or {})
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok"}


@app.post("/tasks/{task_id}/results/move")
def move_direction(task_id: str, filename: str, direction_from: str, direction_to: str):
    if direction_from not in {"upstream", "downstream"} or direction_to not in {
        "upstream",
        "downstream",
    }:
        raise HTTPException(status_code=400, detail="direction must be upstream or downstream")
    if direction_from == direction_to:
        return {"status": "ok", "message": "no change"}
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    src = Path(task.intermediate_dir) / direction_from / filename
    if not src.exists():
        raise HTTPException(status_code=404, detail="file not found")
    dst_dir = Path(task.intermediate_dir) / direction_to
    dst_dir.mkdir(parents=True, exist_ok=True)
    payload = json.loads(src.read_text(encoding="utf-8"))
    payload["direction"] = direction_to
    dst = dst_dir / filename
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    src.unlink(missing_ok=True)
    return {"status": "ok", "message": f"moved to {direction_to}"}


@app.get("/tasks/{task_id}/results/{direction}/export")
def export_for_editing(task_id: str, direction: str):
    """Export current results as Excel for editing."""
    if direction not in {"upstream", "downstream"}:
        raise HTTPException(status_code=400, detail="direction must be upstream or downstream")
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get headers for this direction
    headers = headers_def.upstream_headers if direction == "upstream" else headers_def.downstream_headers

    # Aggregate results into DataFrame
    intermediate_dir = Path(task.intermediate_dir)
    df = aggregate_results(intermediate_dir, headers, direction)

    if df.empty:
        raise HTTPException(status_code=404, detail="No results to export")

    # Write to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        df.to_excel(tmp.name, index=False)
        return FileResponse(
            path=tmp.name,
            filename=f"{task.id}_{direction}_edit.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


@app.post("/tasks/{task_id}/results/{direction}/import")
async def import_from_excel(task_id: str, direction: str, file: UploadFile = File(...)):
    """Import edited Excel to update results."""
    if direction not in {"upstream", "downstream"}:
        raise HTTPException(status_code=400, detail="direction must be upstream or downstream")
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")

    # Read uploaded Excel
    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        df = pd.read_excel(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel: {str(e)}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if "合同源文件" not in df.columns:
        raise HTTPException(status_code=400, detail="Excel must contain '合同源文件' column")

    # Get headers for this direction
    headers = headers_def.upstream_headers if direction == "upstream" else headers_def.downstream_headers

    # Load existing intermediate files to preserve metadata
    intermediate_dir = Path(task.intermediate_dir) / direction
    intermediate_dir.mkdir(parents=True, exist_ok=True)

    updated_count = 0
    created_count = 0

    for _, row in df.iterrows():
        contract_path = row.get("合同源文件", "")
        if not contract_path:
            continue

        # Derive JSON filename from contract path
        contract_stem = Path(contract_path).stem
        json_filename = f"{contract_stem}.json"
        json_path = intermediate_dir / json_filename

        # Extract field values from Excel row
        new_fields = {}
        for h in headers:
            if h in df.columns:
                val = row.get(h)
                # Handle NaN values
                if pd.isna(val):
                    new_fields[h] = None
                else:
                    new_fields[h] = str(val) if val is not None else None

        if json_path.exists():
            # Update existing file
            with json_path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
            payload["fields"].update(new_fields)
            # Ensure direction matches
            payload["direction"] = direction
            with json_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            updated_count += 1
        else:
            # Create new file with minimal structure
            payload = {
                "contract_path": contract_path,
                "direction": direction,
                "my_party": task.my_party,
                "fields": new_fields,
                "raw_extraction": None,
                "classification": {
                    "direction": direction,
                    "confidence": 0.0,
                    "reason": "Imported from Excel",
                    "raw_response": ""
                },
                "prompt_version": "excel_import",
                "notes": "Imported from user-edited Excel"
            }
            with json_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            created_count += 1

    return {
        "status": "ok",
        "updated": updated_count,
        "created": created_count,
        "message": f"Updated {updated_count} records, created {created_count} new records"
    }


@app.post("/tasks/{task_id}/finalize")
def finalize_task(task_id: str, directions: Optional[List[str]] = None):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    dirs = directions or ["upstream", "downstream"]
    settings = _load_settings_for_task(task)
    outputs: Dict[str, Dict[str, str]] = {}
    for d in dirs:
        outputs[d] = {}
        paths = aggregate_to_outputs(
            settings=settings,
            headers=headers_def,
            direction=d,
            basename=f"{task.id}_{d}",
        )
        outputs[d] = {k: str(v) for k, v in paths.items()}
    return {"status": "ok", "outputs": outputs}


@app.get("/tasks/{task_id}/final/{direction}/{fmt}")
def download_final(task_id: str, direction: str, fmt: str):
    if direction not in {"upstream", "downstream"}:
        raise HTTPException(status_code=400, detail="direction must be upstream or downstream")
    if fmt not in {"csv", "xlsx"}:
        raise HTTPException(status_code=400, detail="fmt must be csv or xlsx")
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    final_dir = Path(task.final_dir)
    candidates = sorted(
        final_dir.glob(f"*{direction}*.{fmt}"), key=lambda p: p.stat().st_mtime, reverse=True
    )
    if not candidates:
        raise HTTPException(status_code=404, detail="no finalized file found, please finalize first")
    target = candidates[0]
    return FileResponse(path=target, filename=target.name, media_type="application/octet-stream")


@app.get("/tasks/{task_id}/final/archive")
def download_archive(task_id: str):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    final_dir = Path(task.final_dir)
    if not final_dir.exists():
        raise HTTPException(status_code=404, detail="final dir not found, please finalize first")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
        shutil.make_archive(tmp.name.replace(".zip", ""), "zip", root_dir=final_dir)
        zip_path = tmp.name
    return FileResponse(path=zip_path, filename=f"{task.id}_final.zip", media_type="application/zip")


@app.delete("/tasks/{task_id}")
def delete_task(task_id: str):
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    shutil.rmtree(Path(task.input_dir).parent, ignore_errors=True)
    # remove from index
    data = task_manager._load_index()
    data.pop(task_id, None)
    task_manager._save_index(data)
    return {"status": "ok"}


@app.post("/tasks/{task_id}/reset")
def reset_task(task_id: str):
    """Clear intermediate and final results, keep input files, allow re-processing."""
    try:
        task = task_manager.get_task(task_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Task not found")
    # Clear intermediate results
    intermediate_dir = Path(task.intermediate_dir)
    if intermediate_dir.exists():
        shutil.rmtree(intermediate_dir)
    intermediate_dir.mkdir(parents=True, exist_ok=True)
    (intermediate_dir / "upstream").mkdir(exist_ok=True)
    (intermediate_dir / "downstream").mkdir(exist_ok=True)
    # Clear final outputs
    final_dir = Path(task.final_dir)
    if final_dir.exists():
        shutil.rmtree(final_dir)
    final_dir.mkdir(parents=True, exist_ok=True)
    # Reset task status
    task_manager.update_status(task_id, "created", None)
    # Clear summary
    data = task_manager._load_index()
    if task_id in data:
        data[task_id].summary = None
        task_manager._save_index(data)
    return {"status": "ok", "message": "Task reset, ready for re-processing"}


# NOTE: Static files are served by Vercel, not by this API server.
# Do NOT mount StaticFiles at "/" as it will override API routes.
# If you need to serve frontend locally for testing, use a separate port or:
# FRONTEND_DIR = Path("frontend")
# if FRONTEND_DIR.exists():
#     app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
