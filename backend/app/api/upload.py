import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.content import Content
from app.models.user import User
from app.schemas.content import ContentOut
from app.services.converter import convert_docx_to_markdown, convert_markdown_to_html
from app.services.storage import StorageService, get_storage

router = APIRouter()

ALLOWED_EXTENSIONS = {".docx", ".md", ".markdown"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


@router.post("/upload", response_model=ContentOut, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

    file_content = await file.read()
    if len(file_content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(400, f"File too large. Max size: {settings.MAX_UPLOAD_SIZE // 1024 // 1024}MB")

    title = os.path.splitext(file.filename)[0]

    if ext == ".docx":
        # python-docx requires a real file path; write to a temp file, parse, then clean up
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        try:
            markdown_text, _image_paths = convert_docx_to_markdown(tmp_path)
        finally:
            os.unlink(tmp_path)
    else:
        # Markdown files can be decoded in-memory without touching the filesystem
        markdown_text = file_content.decode("utf-8", errors="replace").strip()

    content_html = convert_markdown_to_html(markdown_text) if markdown_text else ""

    # Persist to configured storage backend (local or S3/MinIO)
    storage = get_storage()
    key = StorageService.generate_key(ext)
    storage.save(file_content, key)

    content = Content(
        title=title,
        content_markdown=markdown_text,
        content_html=content_html,
        source_type="contribution",
        source_file=key,
        status="draft",
        community_id=None,
        created_by_user_id=current_user.id,
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    return content


@router.post("/{content_id}/cover", response_model=ContentOut)
async def upload_cover_image(
    content_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    content = db.query(Content).filter(Content.id == content_id).first()
    if not content:
        raise HTTPException(404, "Content not found")

    if not file.filename:
        raise HTTPException(400, "No filename provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"不支持的图片格式: {ext}。支持: {ALLOWED_IMAGE_EXTENSIONS}")

    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(400, "图片不能超过 10MB")

    storage = get_storage()
    key = StorageService.generate_key(ext, "covers")
    file_url = storage.save(file_content, key)

    content.cover_image = file_url
    db.commit()
    db.refresh(content)
    return content
