from datetime import datetime

from pydantic import BaseModel


class PreprocessScriptCreate(BaseModel):
    name: str
    type: str
    code: str | None = None
    api_config: dict | None = None
    description: str | None = None


class PreprocessScriptOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    type: str
    code: str | None
    api_config: dict | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class PreprocessTaskCreate(BaseModel):
    name: str
    script_id: int
    parent_task_id: int | None = None
    is_label_output: bool = False
    image_scope: dict


class PreprocessTaskOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    script_id: int
    parent_task_id: int | None
    is_label_output: bool
    image_scope: dict
    status: str
    created_at: datetime
    completed_at: datetime | None


class PreprocessResultOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    task_id: int
    image_id: int
    result_content: dict
    manually_modified: bool
    confirmed: bool


class PreprocessResultUpdate(BaseModel):
    result_content: dict


class PreprocessResultConfirm(BaseModel):
    confirmed: bool