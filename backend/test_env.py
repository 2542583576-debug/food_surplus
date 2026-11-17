from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
print("db_host:", settings.db_host)
print("db_name:", settings.db_name)
