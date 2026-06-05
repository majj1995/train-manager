from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.preprocess import (
    PreprocessScriptCreate, PreprocessScriptOut,
    PreprocessTaskCreate, PreprocessTaskOut,
    PreprocessResultOut, PreprocessResultUpdate, PreprocessResultConfirm,
)
from app.services.preprocess_service import (
    create_script, list_scripts, delete_script,
    create_task, list_tasks, delete_task,
    list_results, update_result, confirm_results,
)

router = APIRouter(prefix="/api/preprocess", tags=["preprocess"])


@router.post("/scripts", response_model=PreprocessScriptOut)
def api_create_script(body: PreprocessScriptCreate, db: Session = Depends(get_db)):
    return create_script(db, body)


@router.get("/scripts", response_model=list[PreprocessScriptOut])
def api_list_scripts(db: Session = Depends(get_db)):
    return list_scripts(db)


@router.delete("/scripts/{script_id}")
def api_delete_script(script_id: int, db: Session = Depends(get_db)):
    if not delete_script(db, script_id):
        raise HTTPException(status_code=404, detail="Script not found")
    return {"ok": True}


@router.post("/tasks", response_model=PreprocessTaskOut)
def api_create_task(body: PreprocessTaskCreate, db: Session = Depends(get_db)):
    return create_task(db, body)


@router.get("/tasks", response_model=list[PreprocessTaskOut])
def api_list_tasks(db: Session = Depends(get_db)):
    return list_tasks(db)


@router.delete("/tasks/{task_id}")
def api_delete_task(task_id: int, db: Session = Depends(get_db)):
    if not delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return {"ok": True}


@router.get("/tasks/{task_id}/results", response_model=PaginatedResponse[PreprocessResultOut])
def api_list_results(
    task_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = list_results(db, task_id, page, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.put("/results/{result_id}", response_model=PreprocessResultOut)
def api_update_result(result_id: int, body: PreprocessResultUpdate, db: Session = Depends(get_db)):
    result = update_result(db, result_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    return result


@router.post("/tasks/{task_id}/confirm")
def api_confirm_results(task_id: int, body: PreprocessResultConfirm, db: Session = Depends(get_db)):
    if not body.confirmed:
        return {"created_count": 0}
    created = confirm_results(db, task_id, [])
    return {"created_count": created}