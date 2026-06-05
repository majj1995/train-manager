from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (UniqueConstraint("file_hash", name="uq_image_file_hash"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    image_labels: Mapped[list["ImageLabel"]] = relationship(back_populates="image", cascade="all, delete-orphan")
    preprocess_results: Mapped[list["PreprocessResult"]] = relationship(back_populates="image", cascade="all, delete-orphan")
    corpus_records: Mapped[list["CorpusRecord"]] = relationship(back_populates="image", cascade="all, delete-orphan")
    source_directories: Mapped[list["ImageSourceDirectory"]] = relationship(back_populates="image", cascade="all, delete-orphan")