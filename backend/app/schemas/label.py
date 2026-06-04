from datetime import datetime

from pydantic import BaseModel


class LabelGroupCreate(BaseModel):
    name: str
    description: str | None = None


class LabelGroupOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    created_at: datetime


class LabelCreate(BaseModel):
    name: str
    description: str | None = None
    color: str | None = "#409EFF"
    group_id: int


class LabelOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    description: str | None
    color: str | None
    group_id: int
    created_at: datetime


class ImageLabelCreate(BaseModel):
    image_id: int
    label_id: int
    source: str = "manual"
    confidence: float = 1.0


class ImageLabelOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    image_id: int
    label_id: int
    source: str
    confidence: float
    created_at: datetime


class BatchLabelCreate(BaseModel):
    image_ids: list[int]
    label_id: int
    source: str = "manual"
    confidence: float = 1.0


class BatchLabelDelete(BaseModel):
    image_ids: list[int]
    label_id: int