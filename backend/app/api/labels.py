from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.label import (
    LabelGroupCreate, LabelGroupOut,
    LabelCreate, LabelOut,
    BatchLabelCreate, BatchLabelDelete,
)
from app.services.label_service import (
    create_group, list_groups, delete_group,
    create_label, list_labels, delete_label,
    batch_add_labels, batch_remove_labels,
)

router = APIRouter(prefix="/labels", tags=["labels"])


@router.post("/groups", response_model=LabelGroupOut)
def api_create_group(body: LabelGroupCreate, db: Session = Depends(get_db)):
    return create_group(db, body)


@router.get("/groups", response_model=list[LabelGroupOut])
def api_list_groups(db: Session = Depends(get_db)):
    return list_groups(db)


@router.delete("/groups/{group_id}")
def api_delete_group(group_id: int, db: Session = Depends(get_db)):
    if not delete_group(db, group_id):
        raise HTTPException(status_code=404, detail="Group not found")
    return {"ok": True}


@router.post("/groups/{group_id}/labels", response_model=LabelOut)
def api_create_label(group_id: int, body: LabelCreate, db: Session = Depends(get_db)):
    body.group_id = group_id
    return create_label(db, body)


@router.get("/groups/{group_id}/labels", response_model=list[LabelOut])
def api_list_labels(group_id: int, db: Session = Depends(get_db)):
    return list_labels(db, group_id)


@router.delete("/labels/{label_id}")
def api_delete_label(label_id: int, db: Session = Depends(get_db)):
    if not delete_label(db, label_id):
        raise HTTPException(status_code=404, detail="Label not found")
    return {"ok": True}


@router.post("/batch-add")
def api_batch_add_labels(body: BatchLabelCreate, db: Session = Depends(get_db)):
    added = batch_add_labels(db, body)
    return {"added_count": added}


@router.post("/batch-remove")
def api_batch_remove_labels(body: BatchLabelDelete, db: Session = Depends(get_db)):
    removed = batch_remove_labels(db, body)
    return {"removed_count": removed}