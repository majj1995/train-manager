# 数据源目录管理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 添加数据源目录持久化管理能力，支持添加目录自动导入图片、删除目录智能去重移除图片。

**Architecture:** 新增 SourceDirectory 和 ImageSourceDirectory 两个数据库模型，建立图片与目录的多对多关联。添加目录时自动扫描导入图片并建立关联；删除目录时检查每张图片的关联数，只删除唯一关联的图片。前端 Images.vue 增加"数据源目录"管理卡片。

**Tech Stack:** FastAPI + SQLAlchemy + MySQL (后端), Vue3 + Element Plus (前端)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `backend/app/models/directory.py` | SourceDirectory + ImageSourceDirectory ORM models |
| `backend/app/models/__init__.py` | 导出新模型 |
| `backend/app/models/image.py` | Image 增加 source_directories relationship |
| `backend/app/schemas/directory.py` | 目录相关 Pydantic schemas |
| `backend/app/schemas/__init__.py` | 导出新 schemas |
| `backend/app/services/directory_service.py` | 添加/删除目录的业务逻辑 |
| `backend/app/services/image_service.py` | 修改 import_images 建立目录关联 |
| `backend/app/api/directories.py` | 目录 CRUD API routes |
| `backend/app/main.py` | 注册 directories router |
| `frontend/src/api/directories.js` | 目录 API 调用 |
| `frontend/src/views/Images.vue` | 增加数据源目录管理卡片 |

---

### Task 1: 数据库模型 — SourceDirectory + ImageSourceDirectory

**Files:**
- Create: `backend/app/models/directory.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/image.py`

- [ ] **Step 1: 创建 models/directory.py**

```python
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
```

- [ ] **Step 2: 修改 models/image.py — 添加 source_directories relationship**

在 Image 类中添加：

```python
    source_directories: Mapped[list["ImageSourceDirectory"]] = relationship(back_populates="image", cascade="all, delete-orphan")
```

- [ ] **Step 3: 修改 models/__init__.py — 导出新模型**

添加：

```python
from app.models.directory import SourceDirectory, ImageSourceDirectory
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/models/directory.py backend/app/models/__init__.py backend/app/models/image.py
git commit -m "feat: add SourceDirectory and ImageSourceDirectory ORM models"
```

---

### Task 2: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/directory.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: 创建 schemas/directory.py**

```python
from datetime import datetime
from pydantic import BaseModel


class DirectoryCreate(BaseModel):
    path: str
    recursive: bool = False


class DirectoryOut(BaseModel):
    id: int
    path: str
    recursive: bool
    image_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DirectoryDeleteResult(BaseModel):
    deleted_images_count: int
    kept_images_count: int
```

- [ ] **Step 2: 修改 schemas/__init__.py — 导出新 schemas**

添加：

```python
from app.schemas.directory import DirectoryCreate, DirectoryOut, DirectoryDeleteResult
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/directory.py backend/app/schemas/__init__.py
git commit -m "feat: add directory management Pydantic schemas"
```

---

### Task 3: 目录管理 Service 层

**Files:**
- Create: `backend/app/services/directory_service.py`
- Modify: `backend/app/services/image_service.py`

- [ ] **Step 1: 创建 directory_service.py**

```python
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.directory import SourceDirectory, ImageSourceDirectory
from app.models.image import Image
from app.services.image_service import IMAGE_EXTENSIONS, compute_file_hash, extract_metadata


def add_directory(db: Session, path: str, recursive: bool) -> SourceDirectory:
    dir_path = Path(path)
    if not dir_path.is_dir():
        raise ValueError(f"Directory not found: {path}")

    existing = db.query(SourceDirectory).filter(SourceDirectory.path == path).first()
    if existing:
        raise ValueError(f"Directory already registered: {path}")

    directory = SourceDirectory(path=path, recursive=recursive, image_count=0)
    db.add(directory)
    db.flush()

    if recursive:
        files = [f for f in dir_path.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]
    else:
        files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS]

    imported_count = 0
    for file_path in sorted(files):
        abs_path = str(file_path.resolve())
        file_hash = compute_file_hash(abs_path)

        existing_image = db.query(Image).filter(Image.file_hash == file_hash).first()

        if existing_image:
            assoc_exists = db.query(ImageSourceDirectory).filter(
                ImageSourceDirectory.image_id == existing_image.id,
                ImageSourceDirectory.directory_id == directory.id,
            ).first()
            if not assoc_exists:
                assoc = ImageSourceDirectory(image_id=existing_image.id, directory_id=directory.id)
                db.add(assoc)
                imported_count += 1
        else:
            metadata = extract_metadata(abs_path)
            image = Image(
                file_path=abs_path,
                file_hash=file_hash,
                width=metadata["width"],
                height=metadata["height"],
                format=metadata["format"],
            )
            db.add(image)
            db.flush()
            assoc = ImageSourceDirectory(image_id=image.id, directory_id=directory.id)
            db.add(assoc)
            imported_count += 1

    directory.image_count = imported_count
    db.commit()
    db.refresh(directory)
    return directory


def list_directories(db: Session) -> list[SourceDirectory]:
    return db.query(SourceDirectory).order_by(SourceDirectory.created_at.desc()).all()


def delete_directory(db: Session, directory_id: int) -> dict:
    directory = db.query(SourceDirectory).filter(SourceDirectory.id == directory_id).first()
    if not directory:
        raise ValueError("Directory not found")

    associations = db.query(ImageSourceDirectory).filter(
        ImageSourceDirectory.directory_id == directory_id
    ).all()

    deleted_images_count = 0
    kept_images_count = 0

    for assoc in associations:
        other_count = db.query(ImageSourceDirectory).filter(
            ImageSourceDirectory.image_id == assoc.image_id,
            ImageSourceDirectory.directory_id != directory_id,
        ).count()

        if other_count == 0:
            db.query(Image).filter(Image.id == assoc.image_id).delete()
            deleted_images_count += 1
        else:
            db.delete(assoc)
            kept_images_count += 1

    db.delete(directory)
    db.commit()

    return {
        "deleted_images_count": deleted_images_count,
        "kept_images_count": kept_images_count,
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/directory_service.py
git commit -m "feat: add directory service with add/list/delete logic"
```

---

### Task 4: 目录管理 API 路由

**Files:**
- Create: `backend/app/api/directories.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建 api/directories.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.directory_service import add_directory, list_directories, delete_directory
from app.schemas.directory import DirectoryCreate, DirectoryOut, DirectoryDeleteResult

router = APIRouter(prefix="/api/directories", tags=["directories"])


@router.post("", response_model=DirectoryOut)
def api_add_directory(body: DirectoryCreate, db: Session = Depends(get_db)):
    try:
        return add_directory(db, body.path, body.recursive)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[DirectoryOut])
def api_list_directories(db: Session = Depends(get_db)):
    return list_directories(db)


@router.delete("/{directory_id}", response_model=DirectoryDeleteResult)
def api_delete_directory(directory_id: int, db: Session = Depends(get_db)):
    try:
        result = delete_directory(db, directory_id)
        return DirectoryDeleteResult(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 2: 修改 main.py — 注册 directories router**

在 `from app.api.collect import router as collect_router` 后添加：

```python
from app.api.directories import router as directories_router
```

在 `app.include_router(collect_router)` 后添加：

```python
app.include_router(directories_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/directories.py backend/app/main.py
git commit -m "feat: add directory management API routes"
```

---

### Task 5: 前端 API 层 + Images.vue 改动

**Files:**
- Create: `frontend/src/api/directories.js`
- Modify: `frontend/src/views/Images.vue`

- [ ] **Step 1: 创建 api/directories.js**

```javascript
import api from './index'

export const addDirectory = (data) => api.post('/api/directories', data)
export const listDirectories = () => api.get('/api/directories')
export const deleteDirectory = (id) => api.delete(`/api/directories/${id}`)
```

- [ ] **Step 2: 修改 Images.vue — 在左侧 sidebar 增加"数据源目录"管理卡片**

在现有 `<el-col :span="4">` 中，在标签分组 card 之前增加一个数据源目录 card：

```vue
<el-card header="数据源目录" style="margin-bottom: 12px">
  <el-button type="primary" size="small" @click="showAddDir = true" style="margin-bottom: 8px; width: 100%">添加目录</el-button>
  <div v-for="d in directories" :key="d.id" style="margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center">
    <div>
      <span style="font-size: 13px">{{ d.path }}</span>
      <el-tag size="small" style="margin-left: 4px">{{ d.image_count }}张</el-tag>
    </div>
    <el-button size="small" type="danger" @click="doDeleteDir(d)">删除</el-button>
  </div>
</el-card>

<el-dialog v-model="showAddDir" title="添加数据源目录" width="400px">
  <el-form>
    <el-form-item label="目录路径">
      <el-input v-model="newDirPath" placeholder="/path/to/images" />
    </el-form-item>
    <el-form-item label="递归扫描子目录">
      <el-switch v-model="newDirRecursive" />
    </el-form-item>
  </el-form>
  <template #footer>
    <el-button @click="showAddDir = false">取消</el-button>
    <el-button type="primary" @click="doAddDir">添加</el-button>
  </template>
</el-dialog>
```

在 `<script setup>` 中增加：

```javascript
import { addDirectory, listDirectories, deleteDirectory } from '../api/directories'

const directories = ref([])
const showAddDir = ref(false)
const newDirPath = ref('')
const newDirRecursive = ref(false)

const loadDirectories = async () => {
  const res = await listDirectories()
  directories.value = res.data
}

const doAddDir = async () => {
  await addDirectory({ path: newDirPath.value, recursive: newDirRecursive.value })
  ElMessage.success('目录添加成功')
  showAddDir.value = false
  loadDirectories()
  loadImages()
}

const doDeleteDir = async (d) => {
  try {
    await ElMessageBox.confirm(`删除目录 ${d.path}？将删除 ${d.image_count} 张仅属于该目录的图片。`, '确认删除')
  } catch { return }
  const res = await deleteDirectory(d.id)
  ElMessage.success(`删除 ${res.data.deleted_images_count} 张图片，保留 ${res.data.kept_images_count} 张图片`)
  loadDirectories()
  loadImages()
}
```

在 `onMounted` 中添加 `loadDirectories()` 调用。

需要额外 import `ElMessageBox`：

```javascript
import { ElMessage, ElMessageBox } from 'element-plus'
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/directories.js frontend/src/views/Images.vue
git commit -m "feat: add directory management to frontend with add/delete UI"
```

---

## Self-Review

### Spec Coverage

| Spec Requirement | Covered By |
|---|---|
| 添加目录自动导入图片 | Task 3 (add_directory) + Task 4 (API) |
| 仅处理图片格式文件 | Task 3 (IMAGE_EXTENSIONS filter in add_directory) |
| 去重：已存在图片仅建关联 | Task 3 (existing_image → ImageSourceDirectory only) |
| 删除目录智能去重 | Task 3 (delete_directory: count other associations) |
| count=1 删除图片及级联 | Task 3 (delete Image record) |
| count>1 仅删关联保留图片 | Task 3 (delete assoc only) |
| 目录 CRUD API | Task 4 |
| 前端目录管理卡片 | Task 5 |
| 前端添加/删除目录 | Task 5 (showAddDir dialog + doDeleteDir) |

All requirements covered.

### Placeholder Scan

No TBD, TODO, "implement later", or other placeholder patterns found. All code blocks contain complete implementation code.

### Type Consistency

- `DirectoryDeleteResult.deleted_images_count` and `DirectoryDeleteResult.kept_images_count` match the dict returned by `delete_directory` service ✓
- `DirectoryOut.image_count` matches `SourceDirectory.image_count` field ✓
- `ImageSourceDirectory.image_id` and `directory_id` match FK references ✓
- Frontend `deleteDirectory(d.id)` matches `DELETE /api/directories/{id}` route ✓