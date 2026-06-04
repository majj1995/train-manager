from sqlalchemy.orm import Session

from app.models.label import LabelGroup, Label, ImageLabel
from app.schemas.label import LabelGroupCreate, LabelCreate, BatchLabelCreate, BatchLabelDelete


def create_group(db: Session, data: LabelGroupCreate) -> LabelGroup:
    group = LabelGroup(name=data.name, description=data.description)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_groups(db: Session) -> list[LabelGroup]:
    return db.query(LabelGroup).order_by(LabelGroup.id).all()


def delete_group(db: Session, group_id: int) -> bool:
    group = db.query(LabelGroup).filter(LabelGroup.id == group_id).first()
    if not group:
        return False
    db.delete(group)
    db.commit()
    return True


def create_label(db: Session, data: LabelCreate) -> Label:
    label = Label(
        name=data.name,
        description=data.description,
        color=data.color,
        group_id=data.group_id,
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


def list_labels(db: Session, group_id: int) -> list[Label]:
    return db.query(Label).filter(Label.group_id == group_id).order_by(Label.id).all()


def delete_label(db: Session, label_id: int) -> bool:
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        return False
    db.delete(label)
    db.commit()
    return True


def batch_add_labels(db: Session, data: BatchLabelCreate) -> int:
    existing = set(
        row[0]
        for row in db.query(ImageLabel.image_id)
        .filter(ImageLabel.label_id == data.label_id)
        .all()
    )
    added = 0
    for image_id in data.image_ids:
        if image_id not in existing:
            il = ImageLabel(
                image_id=image_id,
                label_id=data.label_id,
                source=data.source,
                confidence=data.confidence,
            )
            db.add(il)
            existing.add(image_id)
            added += 1
    db.commit()
    return added


def batch_remove_labels(db: Session, data: BatchLabelDelete) -> int:
    removed = db.query(ImageLabel).filter(
        ImageLabel.label_id == data.label_id,
        ImageLabel.image_id.in_(data.image_ids),
    ).delete(synchronize_session="fetch")
    db.commit()
    return removed