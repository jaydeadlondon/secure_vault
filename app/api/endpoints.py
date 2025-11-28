from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.deps import get_current_user
from app.models.user import User
from app.models.file import FileMetadata
from app.services.file_service import (
    upload_encrypted_file,
    download_decrypted_stream,
    delete_file_completely,
)
from app.schemas.file import FileResponse
from pydantic import BaseModel

router = APIRouter()


class UserCreate(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/auth/register")
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == user_in.username)
    res = await db.execute(stmt)
    if res.scalars().first():
        raise HTTPException(400, "Username taken")

    user = User(
        username=user_in.username, hashed_password=get_password_hash(user_in.password)
    )
    db.add(user)
    await db.commit()
    return {"msg": "User created"}


@router.post("/auth/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.username == form_data.username)
    res = await db.execute(stmt)
    user = res.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(400, "Incorrect login or password")

    return {"access_token": create_access_token(user.username), "token_type": "bearer"}


@router.get("/files", response_model=list[FileResponse])
async def list_my_files(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    stmt = (
        select(FileMetadata)
        .where(FileMetadata.user_id == current_user.id)
        .order_by(FileMetadata.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/files/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_file = await upload_encrypted_file(file, current_user.id, db)
    return db_file


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    iterator, filename, content_type = await download_decrypted_stream(
        file_id, current_user.id, db
    )

    return StreamingResponse(
        iterator(),
        media_type=content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_file_completely(file_id, current_user.id, db)
    return {"status": "deleted", "id": file_id}


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}
