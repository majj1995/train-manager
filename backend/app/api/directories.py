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