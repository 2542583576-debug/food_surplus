"""图片上传接口：魔法袋封面图。保存到本地 uploads 目录并通过 /uploads 静态提供。"""
import os
import secrets
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from app.api.deps import get_current_user
from app.core.config import settings
from app.models import User

router = APIRouter(prefix="/api/upload", tags=["图片上传"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
MAX_BYTES = 5 * 1024 * 1024  # 5MB


def mount_uploads(app) -> None:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


@router.post("/image", summary="上传图片（需登录）")
async def upload_image(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="仅支持 jpg/png/webp/gif 图片")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过 5MB")
    if not content:
        raise HTTPException(status_code=400, detail="图片内容为空")

    day = datetime.now().strftime("%Y%m%d")
    folder = os.path.join(settings.UPLOAD_DIR, day)
    os.makedirs(folder, exist_ok=True)
    name = f"{secrets.token_hex(8)}{ext}"
    path = os.path.join(folder, name)
    with open(path, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/{day}/{name}"}
