from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import IMAGE_BASE_DIR
from app.core.database import engine, Base
from app.api.images import router as images_router
from app.api.labels import router as labels_router
from app.api.auth import router as auth_router
from app.api.preprocess import router as preprocess_router
from app.api.corpus import router as corpus_router
from app.api.collect import router as collect_router

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

IMAGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(IMAGE_BASE_DIR)), name="images")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)