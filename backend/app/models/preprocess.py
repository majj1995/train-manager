from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PreprocessScript(Base):
    __tablename__ = "preprocess_scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    tasks: Mapped[list["PreprocessTask"]] = relationship(back_populates="script")


class PreprocessTask(Base):
    __tablename__ = "preprocess_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    script_id: Mapped[int] = mapped_column(Integer, ForeignKey("preprocess_scripts.id"), nullable=False)
    parent_task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("preprocess_tasks.id"), nullable=True)
    is_label_output: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    image_scope: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    script: Mapped["PreprocessScript"] = relationship(back_populates="tasks")
    parent_task: Mapped["PreprocessTask | None"] = relationship(remote_side=[id])
    results: Mapped[list["PreprocessResult"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class PreprocessResult(Base):
    __tablename__ = "preprocess_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("preprocess_tasks.id"), nullable=False)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=False)
    result_content: Mapped[dict] = mapped_column(JSON, nullable=False)
    manually_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    task: Mapped["PreprocessTask"] = relationship(back_populates="results")
    image: Mapped["Image"] = relationship(back_populates="preprocess_results")