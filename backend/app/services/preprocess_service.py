from sqlalchemy.orm import Session

from app.models.label import Label, ImageLabel
from app.models.preprocess import PreprocessScript, PreprocessTask, PreprocessResult
from app.models.image import Image
from app.schemas.preprocess import PreprocessScriptCreate, PreprocessTaskCreate, PreprocessResultUpdate
from app.tasks.engine import start_task_execution


def create_script(db: Session, data: PreprocessScriptCreate) -> PreprocessScript:
    script = PreprocessScript(
        name=data.name,
        type=data.type,
        code=data.code,
        api_config=data.api_config,
        description=data.description,
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


def list_scripts(db: Session) -> list[PreprocessScript]:
    return db.query(PreprocessScript).order_by(PreprocessScript.id).all()


def delete_script(db: Session, script_id: int) -> bool:
    script = db.query(PreprocessScript).filter(PreprocessScript.id == script_id).first()
    if not script:
        return False
    db.delete(script)
    db.commit()
    return True


def create_task(db: Session, data: PreprocessTaskCreate) -> PreprocessTask:
    task = PreprocessTask(
        name=data.name,
        script_id=data.script_id,
        parent_task_id=data.parent_task_id,
        is_label_output=data.is_label_output,
        image_scope=data.image_scope,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    start_task_execution(task.id)
    return task


def list_tasks(db: Session) -> list[PreprocessTask]:
    return db.query(PreprocessTask).order_by(PreprocessTask.id).all()


def delete_task(db: Session, task_id: int) -> bool:
    task = db.query(PreprocessTask).filter(PreprocessTask.id == task_id).first()
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True


def list_results(db: Session, task_id: int, page: int = 1, page_size: int = 20) -> tuple[list[dict], int]:
    query = db.query(PreprocessResult).filter(PreprocessResult.task_id == task_id)
    total = query.count()
    offset = (page - 1) * page_size
    results = query.order_by(PreprocessResult.id).offset(offset).limit(page_size).all()
    items = []
    for r in results:
        image = db.query(Image).filter(Image.id == r.image_id).first()
        items.append({
            "id": r.id,
            "task_id": r.task_id,
            "image_id": r.image_id,
            "file_path": image.file_path if image else None,
            "result_content": r.result_content,
            "manually_modified": r.manually_modified,
            "confirmed": r.confirmed,
        })
    return items, total


def update_result(db: Session, result_id: int, data: PreprocessResultUpdate) -> PreprocessResult | None:
    result = db.query(PreprocessResult).filter(PreprocessResult.id == result_id).first()
    if not result:
        return None
    result.result_content = data.result_content
    result.manually_modified = True
    db.commit()
    db.refresh(result)
    return result


def confirm_results(db: Session, task_id: int, result_ids: list[int]) -> int:
    task = db.query(PreprocessTask).filter(PreprocessTask.id == task_id).first()
    if not task or not task.is_label_output:
        return 0

    created = 0
    for result_id in result_ids:
        result = db.query(PreprocessResult).filter(PreprocessResult.id == result_id).first()
        if not result or result.confirmed:
            continue

        content = result.result_content
        predicted_labels = content.get("predicted_labels", [])
        label_group_id = content.get("label_group_id")

        for label_name in predicted_labels:
            label = db.query(Label).filter(
                Label.name == label_name,
                Label.group_id == label_group_id,
            ).first()
            if not label:
                continue

            existing = db.query(ImageLabel).filter(
                ImageLabel.image_id == result.image_id,
                ImageLabel.label_id == label.id,
                ImageLabel.source == f"preprocess:{task_id}",
            ).first()
            if existing:
                continue

            image_label = ImageLabel(
                image_id=result.image_id,
                label_id=label.id,
                source=f"preprocess:{task_id}",
                confidence=content.get("confidence", 1.0),
            )
            db.add(image_label)
            created += 1

        result.confirmed = True

    db.commit()
    return created