from sqlalchemy.orm import Session

from app.models.label import LabelGroup, Label, ImageLabel
from app.schemas.label import LabelGroupCreate, LabelCreate, LabelUpdate, BatchLabelCreate, BatchLabelDelete


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


def create_label(db: Session, group_id: int, data: LabelCreate) -> Label:
    if data.parent_id is not None:
        parent = db.query(Label).filter(Label.id == data.parent_id).first()
        if parent and parent.group_id != group_id:
            raise ValueError("parent_id must belong to the same group")
    label = Label(
        name=data.name,
        description=data.description,
        color=data.color,
        group_id=group_id,
        parent_id=data.parent_id,
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    return label


def update_label(db: Session, label_id: int, data: LabelUpdate) -> Label:
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        raise ValueError("Label not found")
    if data.parent_id is not None:
        parent = db.query(Label).filter(Label.id == data.parent_id).first()
        if parent and parent.group_id != label.group_id:
            raise ValueError("parent_id must belong to the same group")
        if data.parent_id == label_id:
            raise ValueError("parent_id cannot be self")
    if data.name is not None:
        label.name = data.name
    if data.description is not None:
        label.description = data.description
    if data.color is not None:
        label.color = data.color
    if data.parent_id is not None:
        label.parent_id = data.parent_id
    db.commit()
    db.refresh(label)
    return label


def list_labels(db: Session, group_id: int) -> list[Label]:
    return db.query(Label).filter(Label.group_id == group_id).order_by(Label.id).all()


def get_label_tree(db: Session, group_id: int) -> list[dict]:
    labels = db.query(Label).filter(Label.group_id == group_id).order_by(Label.id).all()
    label_map = {}
    for label in labels:
        label_map[label.id] = {
            "id": label.id,
            "name": label.name,
            "description": label.description,
            "color": label.color,
            "group_id": label.group_id,
            "parent_id": label.parent_id,
            "children": [],
        }
    tree = []
    for label in labels:
        node = label_map[label.id]
        if label.parent_id and label.parent_id in label_map:
            label_map[label.parent_id]["children"].append(node)
        else:
            tree.append(node)
    return tree


def delete_label(db: Session, label_id: int) -> bool:
    label = db.query(Label).filter(Label.id == label_id).first()
    if not label:
        return False
    children = db.query(Label).filter(Label.parent_id == label_id).all()
    for child in children:
        child.parent_id = None
    db.delete(label)
    db.commit()
    return True


def batch_add_labels(db: Session, data: BatchLabelCreate) -> int:
    existing_pairs = set(
        (row[0], row[1])
        for row in db.query(ImageLabel.image_id, ImageLabel.label_id)
        .filter(ImageLabel.label_id.in_(data.label_ids))
        .all()
    )
    added = 0
    for image_id in data.image_ids:
        for label_id in data.label_ids:
            if (image_id, label_id) not in existing_pairs:
                il = ImageLabel(
                    image_id=image_id,
                    label_id=label_id,
                    source=data.source,
                    confidence=data.confidence,
                )
                db.add(il)
                existing_pairs.add((image_id, label_id))
                added += 1
    db.commit()
    return added


def batch_remove_labels(db: Session, data: BatchLabelDelete) -> int:
    removed = db.query(ImageLabel).filter(
        ImageLabel.label_id.in_(data.label_ids),
        ImageLabel.image_id.in_(data.image_ids),
    ).delete(synchronize_session="fetch")
    db.commit()
    return removed
