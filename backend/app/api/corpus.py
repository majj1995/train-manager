from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.corpus import (
    CorpusTemplateCreate, CorpusTemplateUpdate, CorpusTemplateOut,
    CorpusGenerateRequest, CorpusRecordOut, CorpusRecordUpdate,
    CorpusExportRequest,
)
from app.services.corpus_service import (
    create_template, list_templates, update_template, delete_template,
    generate_corpus, list_records, update_record, confirm_records, export_corpus,
)

router = APIRouter(prefix="/api/corpus", tags=["corpus"])


@router.post("/templates", response_model=CorpusTemplateOut)
def api_create_template(body: CorpusTemplateCreate, db: Session = Depends(get_db)):
    return create_template(db, body)


@router.get("/templates", response_model=list[CorpusTemplateOut])
def api_list_templates(db: Session = Depends(get_db)):
    return list_templates(db)


@router.put("/templates/{template_id}", response_model=CorpusTemplateOut)
def api_update_template(template_id: int, body: CorpusTemplateUpdate, db: Session = Depends(get_db)):
    template = update_template(db, template_id, body)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete("/templates/{template_id}")
def api_delete_template(template_id: int, db: Session = Depends(get_db)):
    if not delete_template(db, template_id):
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True}


@router.post("/generate", response_model=list[CorpusRecordOut])
def api_generate_corpus(body: CorpusGenerateRequest, db: Session = Depends(get_db)):
    try:
        records = generate_corpus(db, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return records


@router.get("/records", response_model=PaginatedResponse[CorpusRecordOut])
def api_list_records(
    group_id: int | None = Query(None),
    template_id: int | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = list_records(db, group_id, template_id, status, page, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.put("/records/{record_id}", response_model=CorpusRecordOut)
def api_update_record(record_id: int, body: CorpusRecordUpdate, db: Session = Depends(get_db)):
    record = update_record(db, record_id, body.output_text)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/records/confirm")
def api_confirm_records(body: list[int], db: Session = Depends(get_db)):
    count = confirm_records(db, body)
    return {"confirmed_count": count}


@router.post("/export")
def api_export_corpus(body: CorpusExportRequest, db: Session = Depends(get_db)):
    filepath = export_corpus(db, body.output_dir, body.group_id, body.template_id, body.status)
    return {"filepath": filepath}