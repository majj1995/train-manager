from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SourceDirectory(Base):
    __tablename__ = "source_directories"
    __table_args__ = (UniqueConstraint("path", name="uq_source_directory_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(500), nullable=False)
    recursive: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    image_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    image_associations: Mapped[list["ImageSourceDirectory"]] = relationship(back_populates="directory", cascade="all, delete-orphan")


class ImageSourceDirectory(Base):
    __tablename__ = "image_source_directories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=False)
    directory_id: Mapped[int] = mapped_column(Integer, ForeignKey("source_directories.id"), nullable=False)

    image: Mapped["Image"] = relationship(back_populates="source_directories")
    directory: Mapped["SourceDirectory"] = relationship(back_populates="image_associations")