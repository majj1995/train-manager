from datetime import datetime
from pydantic import BaseModel


class DirectoryCreate(BaseModel):
    path: str
    recursive: bool = False


class DirectoryOut(BaseModel):
    id: int
    path: str
    recursive: bool
    image_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DirectoryDeleteResult(BaseModel):
    deleted_images_count: int
    kept_images_count: int