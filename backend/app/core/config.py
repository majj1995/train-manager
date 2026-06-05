import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMAGE_BASE_DIR = Path(os.getenv("IMAGE_BASE_DIR", str(BASE_DIR / "data" / "images")))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://ppsma:D%40%23evc2134@localhost:3306/auto_train"
)

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24