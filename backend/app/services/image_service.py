import hashlib
from pathlib import Path

from PIL import Image as PILImage
from sqlalchemy.orm import Session, joinedload

from app.core.database import SessionLocal
from app.models.image import Image
from app.core.database import SessionLocal
from app.models.label import ImageLabel, Label
from app.models.directory import ImageSourceDirectory
from app.schemas.image import ImageImportResult


def compute_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def extract_metadata(file_path: str) -> dict:
    try:
        with PILImage.open(file_path) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
            }
    except Exception:
        return {"width": None, "height": None, "format": None}


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}


def import_images(directory: str, recursive: bool = False) -> ImageImportResult:
    db = SessionLocal()
    try:
        source_dir = Path(directory)
        if not source_dir.is_dir():
            raise ValueError(f"Directory not found: {directory}")

        if recursive:
            files = [
                f for f in source_dir.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            ]
        else:
            files = [
                f for f in source_dir.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
            ]

        imported_count = 0
        skipped_count = 0
        failed_paths = []

        existing_hashes = set(
            row[0] for row in db.query(Image.file_hash).all()
        )

        for file_path in sorted(files):
            try:
                file_hash = compute_file_hash(str(file_path))
                if file_hash in existing_hashes:
                    skipped_count += 1
                    continue

                metadata = extract_metadata(str(file_path))

                image = Image(
                    file_path=str(file_path),
                    file_hash=file_hash,
                    width=metadata["width"],
                    height=metadata["height"],
                    format=metadata["format"],
                )
                db.add(image)
                existing_hashes.add(file_hash)
                imported_count += 1
            except Exception:
                failed_paths.append(str(file_path))

        db.commit()
        return ImageImportResult(
            imported_count=imported_count,
            skipped_count=skipped_count,
            failed_count=len(failed_paths),
            failed_paths=failed_paths,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def list_images(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    group_id: int | None = None,
    label_id: int | None = None,
    directory_id: int | None = None,
) -> tuple[list[Image], int]:
    query = db.query(Image)

    if label_id is not None:
        query = query.join(ImageLabel, Image.id == ImageLabel.image_id).filter(
            ImageLabel.label_id == label_id
        )

    if group_id is not None:
        query = query.join(ImageLabel, Image.id == ImageLabel.image_id).join(
            Label, ImageLabel.label_id == Label.id
        ).filter(Label.group_id == group_id)

    if directory_id is not None:
        query = query.join(ImageSourceDirectory, Image.id == ImageSourceDirectory.image_id).filter(
            ImageSourceDirectory.directory_id == directory_id
        )

    total = query.count()
    offset = (page - 1) * page_size
    images = query.order_by(Image.id).offset(offset).limit(page_size).all()
    return images, total


def get_image_detail(db: Session, image_id: int) -> Image | None:
    return db.query(Image).options(
        joinedload(Image.image_labels).joinedload(ImageLabel.label).joinedload(Label.group)
    ).filter(Image.id == image_id).first()