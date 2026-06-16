from datetime import datetime

from pydantic import BaseModel


class ImageCreate(BaseModel):
    file_path: str
    file_hash: str
    width: int | None = None
    height: int | None = None
    format: str | None = None


class ImageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    file_path: str
    file_hash: str
    width: int | None
    height: int | None
    format: str | None
    created_at: datetime


class ImageImport(BaseModel):
    directory: str
    recursive: bool = False


class ImageImportResult(BaseModel):
    imported_count: int
    skipped_count: int
    failed_count: int
    failed_paths: list[str] = []


class ImageDeleteByIds(BaseModel):
    image_ids: list[int]


class ImageDeleteByPath(BaseModel):
    path_prefix: str


class ImageDeleteResult(BaseModel):
    deleted_count: int