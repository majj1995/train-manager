from datetime import datetime, timezone

from sqlalchemy import Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LabelGroup(Base):
    __tablename__ = "label_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    labels: Mapped[list["Label"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class Label(Base):
    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True, default="#409EFF")
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("label_groups.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    group: Mapped["LabelGroup"] = relationship(back_populates="labels")
    image_labels: Mapped[list["ImageLabel"]] = relationship(back_populates="label")


class ImageLabel(Base):
    __tablename__ = "image_labels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_id: Mapped[int] = mapped_column(Integer, ForeignKey("images.id"), nullable=False)
    label_id: Mapped[int] = mapped_column(Integer, ForeignKey("labels.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="manual")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    image: Mapped["Image"] = relationship(back_populates="image_labels")
    label: Mapped["Label"] = relationship(back_populates="image_labels")