from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from app.core.config import IMAGE_BASE_DIR
from app.core.database import engine, Base, SessionLocal
from app.api.images import router as images_router
from app.api.labels import router as labels_router
from app.api.auth import router as auth_router
from app.api.preprocess import router as preprocess_router
from app.api.corpus import router as corpus_router
from app.api.collect import router as collect_router
from app.api.directories import router as directories_router
from app.models.image import Image

app = FastAPI(title="Auto-Train Data Management", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images_router)
app.include_router(labels_router)
app.include_router(auth_router)
app.include_router(preprocess_router)
app.include_router(corpus_router)
app.include_router(collect_router)
app.include_router(directories_router)

IMAGE_BASE_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/images/{filename}")
def serve_image(filename: str):
    db = SessionLocal()
    image = db.query(Image).filter(Image.file_path.like(f"%/{filename}")).first()
    db.close()
    if not image:
        return None
    file_path = Path(image.file_path)
    if not file_path.is_file():
        return None
    return FileResponse(str(file_path))


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)