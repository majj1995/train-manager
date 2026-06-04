from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CorpusTemplate(Base):
    __tablename__ = "corpus_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    corpus_records: Mapped[list["CorpusRecord"]] = relationship(back_populates="template")


class CorpusRecord(Base):
    __tablename__ = "corpus_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=False)
    template_id: Mapped[int] = mapped_column(Integer, ForeignKey("corpus_templates.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("label_groups.id"), nullable=False)
    task_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("preprocess_tasks.id"), nullable=True)
    output_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    image: Mapped["Image"] = relationship(back_populates="corpus_records")
    template: Mapped["CorpusTemplate"] = relationship(back_populates="corpus_records")
    group: Mapped["LabelGroup"] = relationship()
    task: Mapped["PreprocessTask | None"] = relationship()