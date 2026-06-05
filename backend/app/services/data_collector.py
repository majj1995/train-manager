from abc import ABC, abstractmethod
from pathlib import Path
import shutil

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}


class DataCollector(ABC):
    @abstractmethod
    def collect(self, target_dir: Path) -> list[str]:
        ...


class LocalDirectoryCollector(DataCollector):
    def __init__(self, source_dir: Path):
        self.source_dir = source_dir

    def collect(self, target_dir: Path) -> list[str]:
        target_dir.mkdir(parents=True, exist_ok=True)
        collected = []
        for f in self.source_dir.iterdir():
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                dest = target_dir / f.name
                shutil.copy2(f, dest)
                collected.append(str(dest))
        return collected