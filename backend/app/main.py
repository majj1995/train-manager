from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import IMAGE_BASE_DIR
from app.core.database import engine, Base

app = FastAPI(title="Auto-Train Data Management", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

IMAGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/images", StaticFiles(directory=str(IMAGE_BASE_DIR)), name="images")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)