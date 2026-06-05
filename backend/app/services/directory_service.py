from pathlib import Path

from sqlalchemy.orm import Session

from app.models.directory import SourceDirectory, ImageSourceDirectory
from app.models.image import Image
from app.services.image_service import IMAGE_EXTENSIONS, compute_file_hash, extract_metadata


def add_directory(db: Session, path: str, recursive: bool) -> SourceDirectory:
    dir_path = Path(path)
    if not dir_path.is_dir():
        raise ValueError(f"Directory not found: {path}")

    existing = db.query(SourceDirectory).filter(SourceDirectory.path == path).first()
    if existing:
        raise ValueError(f"Directory already registered: {path}")

    directory = SourceDirectory(path=path, recursive=recursive, image_count=0)
    db.add(directory)
    db.flush()

    if recursive:
        files = [f for f in dir_path.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
    else:
        files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]

    imported_count = 0
    for file_path in sorted(files):
        abs_path = str(file_path.resolve())
        file_hash = compute_file_hash(abs_path)

        existing_image = db.query(Image).filter(Image.file_hash == file_hash).first()

        if existing_image:
            assoc_exists = db.query(ImageSourceDirectory).filter(
                ImageSourceDirectory.image_id == existing_image.id,
                ImageSourceDirectory.directory_id == directory.id,
            ).first()
            if not assoc_exists:
                assoc = ImageSourceDirectory(image_id=existing_image.id, directory_id=directory.id)
                db.add(assoc)
                imported_count += 1
        else:
            metadata = extract_metadata(abs_path)
            image = Image(
                file_path=abs_path,
                file_hash=file_hash,
                width=metadata["width"],
                height=metadata["height"],
                format=metadata["format"],
            )
            db.add(image)
            db.flush()
            assoc = ImageSourceDirectory(image_id=image.id, directory_id=directory.id)
            db.add(assoc)
            imported_count += 1

    directory.image_count = imported_count
    db.commit()
    db.refresh(directory)
    return directory


def list_directories(db: Session) -> list[SourceDirectory]:
    return db.query(SourceDirectory).order_by(SourceDirectory.created_at.desc()).all()


def delete_directory(db: Session, directory_id: int) -> dict:
    directory = db.query(SourceDirectory).filter(SourceDirectory.id == directory_id).first()
    if not directory:
        raise ValueError("Directory not found")

    associations = db.query(ImageSourceDirectory).filter(
        ImageSourceDirectory.directory_id == directory_id
    ).all()

    deleted_images_count = 0
    kept_images_count = 0

    for assoc in associations:
        other_count = db.query(ImageSourceDirectory).filter(
            ImageSourceDirectory.image_id == assoc.image_id,
            ImageSourceDirectory.directory_id != directory_id,
        ).count()

        if other_count == 0:
            db.query(Image).filter(Image.id == assoc.image_id).delete()
            deleted_images_count += 1
        else:
            db.delete(assoc)
            kept_images_count += 1

    db.delete(directory)
    db.commit()

    return {
        "deleted_images_count": deleted_images_count,
        "kept_images_count": kept_images_count,
    }