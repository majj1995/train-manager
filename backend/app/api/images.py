from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.image import ImageImport, ImageImportResult, ImageOut, ImageDeleteByIds, ImageDeleteByPath, ImageDeleteResult
from app.schemas.label import LabelOut
from app.models.image import Image
from app.models.label import ImageLabel, Label
from app.models.directory import ImageSourceDirectory
from app.services.image_service import import_images, get_image_detail, delete_images_by_ids, delete_images_by_path_prefix

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/import", response_model=ImageImportResult)
def api_import_images(body: ImageImport):
    return import_images(body.directory, body.recursive)


@router.get("/", response_model=PaginatedResponse)
def api_list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    group_id: int | None = Query(None),
    label_id: int | None = Query(None),
    directory_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Image)

    if label_id is not None:
        query = query.join(ImageLabel, Image.id == ImageLabel.image_id).filter(
            ImageLabel.label_id == label_id
        ).distinct()

    if directory_id is not None:
        query = query.join(ImageSourceDirectory, Image.id == ImageSourceDirectory.image_id).filter(
            ImageSourceDirectory.directory_id == directory_id
        )

    total = query.count()
    offset = (page - 1) * page_size
    images = query.order_by(Image.id).offset(offset).limit(page_size).all()

    items = []
    for img in images:
        tag_list = []
        label_query = db.query(ImageLabel).filter(ImageLabel.image_id == img.id)
        if group_id is not None:
            label_query = label_query.join(Label, ImageLabel.label_id == Label.id).filter(
                Label.group_id == group_id
            )
        for il in label_query.all():
            tag_list.append({
                "id": il.label.id,
                "name": il.label.name,
                "color": il.label.color,
                "group_id": il.label.group_id,
                "source": il.source,
                "confidence": il.confidence,
            })

        items.append({
            "id": img.id,
            "file_path": img.file_path,
            "file_hash": img.file_hash,
            "width": img.width,
            "height": img.height,
            "format": img.format,
            "created_at": img.created_at,
            "tags": tag_list,
        })

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{image_id}")
def api_get_image_detail(image_id: int, db: Session = Depends(get_db)):
    image = get_image_detail(db, image_id)
    if not image:
        return None
    label_data = []
    for il in image.image_labels:
        label_data.append({
            "image_label_id": il.id,
            "label": LabelOut.model_validate(il.label),
            "group": {"id": il.label.group.id, "name": il.label.group.name},
            "source": il.source,
            "confidence": il.confidence,
        })
    return {
        "id": image.id,
        "file_path": image.file_path,
        "file_hash": image.file_hash,
        "width": image.width,
        "height": image.height,
        "format": image.format,
        "created_at": image.created_at,
        "labels": label_data,
    }


@router.post("/delete-by-ids", response_model=ImageDeleteResult)
def api_delete_images_by_ids(body: ImageDeleteByIds, db: Session = Depends(get_db)):
    count = delete_images_by_ids(db, body.image_ids)
    return ImageDeleteResult(deleted_count=count)


@router.post("/delete-by-path", response_model=ImageDeleteResult)
def api_delete_images_by_path(body: ImageDeleteByPath, db: Session = Depends(get_db)):
    count = delete_images_by_path_prefix(db, body.path_prefix)
    return ImageDeleteResult(deleted_count=count)
