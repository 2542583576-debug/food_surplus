"""兼容旧入口：统一使用 app.core.config 中的全局配置。"""
from app.core.config import settings  # noqa: F401

__all__ = ["settings"]
