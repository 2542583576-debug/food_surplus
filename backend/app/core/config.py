from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置：全部来自环境变量或 .env，禁止在代码中硬编码密钥。"""

    # 应用
    APP_NAME: str = "惜食余量魔法袋"
    DEBUG: bool = False
    SECRET_KEY: str = "dev-only-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    # MySQL
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "food_surplus"
    DATABASE_URL_OVERRIDE: Optional[str] = None

    # Redis（可选，未配置/未启动时系统自动降级为本地内存）
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL_OVERRIDE: Optional[str] = None
    REDIS_ENABLED: bool = True

    # 跨域：生产环境必须显式配置来源，不建议 "*"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 图片上传目录（相对项目根目录或绝对路径）
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def DATABASE_URL(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_URL_OVERRIDE:
            return self.REDIS_URL_OVERRIDE
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.CORS_ORIGINS.split(",") if item.strip()]

    # 兼容早期代码使用的小写命名
    @property
    def db_host(self) -> str:
        return self.MYSQL_HOST

    @property
    def db_port(self) -> int:
        return self.MYSQL_PORT

    @property
    def db_user(self) -> str:
        return self.MYSQL_USER

    @property
    def db_password(self) -> str:
        return self.MYSQL_PASSWORD

    @property
    def db_name(self) -> str:
        return self.MYSQL_DB


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
