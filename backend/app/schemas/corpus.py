from datetime import datetime

from pydantic import BaseModel


class CorpusTemplateCreate(BaseModel):
    name: str
    template_content: str
    description: str | None = None


class CorpusTemplateUpdate(BaseModel):
    name: str | None = None
    template_content: str | None = None
    description: str | None = None


class CorpusTemplateOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    template_content: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class CorpusGenerateRequest(BaseModel):
    template_id: int
    group_id: int
    task_id: int | None = None
    label_ids: list[int] | None = None


class CorpusRecordOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    image_id: int
    template_id: int
    group_id: int
    task_id: int | None
    output_text: str
    status: str
    created_at: datetime


class CorpusRecordUpdate(BaseModel):
    output_text: str
    status: str | None = None


class CorpusExportRequest(BaseModel):
    output_dir: str
    group_id: int | None = None
    template_id: int | None = None
    status: str | None = None