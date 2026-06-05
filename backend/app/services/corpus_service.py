import json
import os
from datetime import datetime
from pathlib import Path

from jinja2 import Template, TemplateError
from sqlalchemy.orm import Session

from app.models.corpus import CorpusTemplate, CorpusRecord
from app.models.image import Image
from app.models.label import LabelGroup, Label, ImageLabel
from app.models.preprocess import PreprocessResult
from app.schemas.corpus import CorpusTemplateCreate, CorpusTemplateUpdate, CorpusGenerateRequest


def create_template(db: Session, data: CorpusTemplateCreate) -> CorpusTemplate:
    template = CorpusTemplate(
        name=data.name,
        template_content=data.template_content,
        description=data.description,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def list_templates(db: Session) -> list[CorpusTemplate]:
    return db.query(CorpusTemplate).order_by(CorpusTemplate.id).all()


def update_template(db: Session, template_id: int, data: CorpusTemplateUpdate) -> CorpusTemplate | None:
    template = db.query(CorpusTemplate).filter(CorpusTemplate.id == template_id).first()
    if not template:
        return None
    if data.name is not None:
        template.name = data.name
    if data.template_content is not None:
        template.template_content = data.template_content
    if data.description is not None:
        template.description = data.description
    db.commit()
    db.refresh(template)
    return template


def delete_template(db: Session, template_id: int) -> bool:
    template = db.query(CorpusTemplate).filter(CorpusTemplate.id == template_id).first()
    if not template:
        return False
    db.delete(template)
    db.commit()
    return True


def generate_corpus(db: Session, data: CorpusGenerateRequest) -> list[CorpusRecord]:
    template_obj = db.query(CorpusTemplate).filter(CorpusTemplate.id == data.template_id).first()
    if not template_obj:
        raise ValueError("Template not found")

    group = db.query(LabelGroup).filter(LabelGroup.id == data.group_id).first()
    if not group:
        raise ValueError("Label group not found")

    jinja_template = Template(template_obj.template_content)

    query = db.query(Image).join(
        ImageLabel, Image.id == ImageLabel.image_id
    ).join(
        Label, ImageLabel.label_id == Label.id
    ).filter(Label.group_id == data.group_id)

    if data.label_ids:
        query = query.filter(ImageLabel.label_id.in_(data.label_ids))

    images = query.distinct().all()

    records = []
    for image in images:
        image_labels = db.query(ImageLabel).filter(
            ImageLabel.image_id == image.id
        ).join(Label, ImageLabel.label_id == Label.id).filter(
            Label.group_id == data.group_id
        ).all()
        label_names = [il.label.name for il in image_labels]

        result_content = None
        if data.task_id:
            preprocess_result = db.query(PreprocessResult).filter(
                PreprocessResult.image_id == image.id,
                PreprocessResult.task_id == data.task_id,
            ).first()
            if preprocess_result:
                result_content = preprocess_result.result_content

        context = {
            "image": {"id": image.id, "file_path": image.file_path, "width": image.width, "height": image.height},
            "labels": label_names,
            "label_group_name": group.name,
            "result_content": result_content,
        }

        try:
            output_text = jinja_template.render(**context)
        except TemplateError as e:
            raise ValueError(f"Template rendering error for image {image.id}: {e}")

        record = CorpusRecord(
            image_id=image.id,
            template_id=data.template_id,
            group_id=data.group_id,
            task_id=data.task_id,
            output_text=output_text,
            status="draft",
        )
        db.add(record)
        records.append(record)

    db.commit()
    for r in records:
        db.refresh(r)
    return records


def list_records(
    db: Session,
    group_id: int | None = None,
    template_id: int | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[CorpusRecord], int]:
    query = db.query(CorpusRecord)
    if group_id is not None:
        query = query.filter(CorpusRecord.group_id == group_id)
    if template_id is not None:
        query = query.filter(CorpusRecord.template_id == template_id)
    if status is not None:
        query = query.filter(CorpusRecord.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    items = query.order_by(CorpusRecord.id).offset(offset).limit(page_size).all()
    return items, total


def update_record(db: Session, record_id: int, output_text: str) -> CorpusRecord | None:
    record = db.query(CorpusRecord).filter(CorpusRecord.id == record_id).first()
    if not record:
        return None
    record.output_text = output_text
    db.commit()
    db.refresh(record)
    return record


def confirm_records(db: Session, record_ids: list[int]) -> int:
    count = 0
    for record_id in record_ids:
        record = db.query(CorpusRecord).filter(CorpusRecord.id == record_id).first()
        if record and record.status == "draft":
            record.status = "confirmed"
            count += 1
    db.commit()
    return count


def export_corpus(
    db: Session,
    output_dir: str,
    group_id: int | None = None,
    template_id: int | None = None,
    status: str | None = None,
) -> str:
    query = db.query(CorpusRecord)
    if group_id is not None:
        query = query.filter(CorpusRecord.group_id == group_id)
    if template_id is not None:
        query = query.filter(CorpusRecord.template_id == template_id)
    if status is not None:
        query = query.filter(CorpusRecord.status == status)
    else:
        query = query.filter(CorpusRecord.status == "confirmed")

    records = query.order_by(CorpusRecord.id).all()

    sharegpt_entries = []
    for record in records:
        try:
            entry = json.loads(record.output_text)
        except json.JSONDecodeError:
            continue

        image = db.query(Image).filter(Image.id == record.image_id).first()
        if image:
            _replace_image_paths(entry, Path(image.file_path).name)

        sharegpt_entry = {
            "conversations": [
                {"from": "human", "value": entry.get("instruction", entry.get("input", ""))},
                {"from": "gpt", "value": entry.get("output", "")},
            ],
            "images": [Path(image.file_path).name] if image else [],
        }
        sharegpt_entries.append(sharegpt_entry)

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sharegpt_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(sharegpt_entries, f, ensure_ascii=False, indent=2)

    for record in records:
        record.status = "exported"
    db.commit()

    return filepath


def _replace_image_paths(obj: dict | list, filename: str):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and _looks_like_absolute_image_path(value):
                obj[key] = filename
            elif isinstance(value, (dict, list)):
                _replace_image_paths(value, filename)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str) and _looks_like_absolute_image_path(item):
                obj[i] = filename
            elif isinstance(item, (dict, list)):
                _replace_image_paths(item, filename)


def _looks_like_absolute_image_path(value: str) -> bool:
    return "/" in value and any(value.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"))