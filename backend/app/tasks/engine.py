import asyncio
import json
import subprocess
import tempfile
import threading
from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.image import Image
from app.models.label import Label, ImageLabel
from app.models.preprocess import PreprocessScript, PreprocessTask, PreprocessResult


def resolve_image_scope(db: Session, scope: dict) -> list[int]:
    scope_type = scope.get("type", "all")
    if scope_type == "all":
        rows = db.query(Image.id).all()
        return [r[0] for r in rows]
    elif scope_type == "by_labels":
        label_ids = scope.get("label_ids", [])
        rows = (
            db.query(Image.id)
            .join(ImageLabel, Image.id == ImageLabel.image_id)
            .filter(ImageLabel.label_id.in_(label_ids))
            .distinct()
            .all()
        )
        return [r[0] for r in rows]
    elif scope_type == "manual":
        return scope.get("image_ids", [])
    return []


def get_parent_results(db: Session, parent_task_id: int | None) -> dict[int, dict]:
    if parent_task_id is None:
        return {}
    results = db.query(PreprocessResult).filter(
        PreprocessResult.task_id == parent_task_id
    ).all()
    return {r.image_id: r.result_content for r in results}


def run_local_python_script(code: str, input_data: dict, timeout: int = 300) -> dict:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as infile:
        json.dump(input_data, infile)
        infile_path = infile.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as outfile:
        outfile_path = outfile.name

    script = (
        f"import json, sys\n"
        f"with open('{infile_path}', 'r') as f:\n"
        f"    _input = json.load(f)\n"
        f"{code}\n"
        f"with open('{outfile_path}', 'w') as f:\n"
        f"    json.dump(_output, f)\n"
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as scriptfile:
        scriptfile.write(script)
        scriptfile_path = scriptfile.name

    try:
        proc = subprocess.run(
            ["python", scriptfile_path],
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Script failed: {proc.stderr}")
        with open(outfile_path, "r") as f:
            return json.load(f)
    except subprocess.TimeoutExpired:
        raise RuntimeError("Script execution timed out")
    finally:
        import os
        for p in [infile_path, outfile_path, scriptfile_path]:
            if os.path.exists(p):
                os.unlink(p)


async def run_model_api(api_config: dict, input_data: dict) -> dict:
    url = api_config.get("url", "")
    method = api_config.get("method", "POST").upper()
    headers = api_config.get("headers", {})
    timeout_sec = api_config.get("timeout", 60)

    async with httpx.AsyncClient(timeout=timeout_sec) as client:
        if method == "POST":
            resp = await client.post(url, json=input_data, headers=headers)
        elif method == "GET":
            resp = await client.get(url, params=input_data, headers=headers)
        else:
            resp = await client.request(method, url, json=input_data, headers=headers)
        resp.raise_for_status()
        return resp.json()


async def execute_task(task_id: int):
    db = SessionLocal()
    try:
        task = db.query(PreprocessTask).filter(PreprocessTask.id == task_id).first()
        if not task:
            return

        task.status = "running"
        db.commit()

        script = db.query(PreprocessScript).filter(PreprocessScript.id == task.script_id).first()
        if not script:
            task.status = "failed"
            db.commit()
            return

        image_ids = resolve_image_scope(db, task.image_scope)
        parent_results = get_parent_results(db, task.parent_task_id)

        for image_id in image_ids:
            image = db.query(Image).filter(Image.id == image_id).first()
            if not image:
                continue

            input_data = {
                "image_id": image.id,
                "file_path": image.file_path,
                "width": image.width,
                "height": image.height,
                "format": image.format,
            }
            if image_id in parent_results:
                input_data["parent_result"] = parent_results[image_id]

            try:
                if script.type == "local_python":
                    result_content = run_local_python_script(script.code, input_data)
                elif script.type == "model_api":
                    result_content = await run_model_api(script.api_config, input_data)
                else:
                    continue

                existing = db.query(PreprocessResult).filter(
                    PreprocessResult.task_id == task_id,
                    PreprocessResult.image_id == image_id,
                ).first()
                if existing:
                    existing.result_content = result_content
                else:
                    result = PreprocessResult(
                        task_id=task_id,
                        image_id=image_id,
                        result_content=result_content,
                    )
                    db.add(result)
                db.commit()
            except Exception:
                db.rollback()
                continue

        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        try:
            task = db.query(PreprocessTask).filter(PreprocessTask.id == task_id).first()
            if task:
                task.status = "failed"
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def start_task_execution(task_id: int):
    def _run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(execute_task(task_id))
        finally:
            loop.close()

    t = threading.Thread(target=_run, daemon=True)
    t.start()