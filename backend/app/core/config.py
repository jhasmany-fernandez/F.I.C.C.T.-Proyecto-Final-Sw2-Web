from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Base de datos
    database_url: str = "postgresql://heatmapper_user:password@db:5432/heatmapper"

    # Seguridad JWT
    secret_key: str = "cambia_esto_por_un_secreto_seguro"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Servidor
    debug: bool = False
    cors_origins: list[str] = ["http://localhost", "http://localhost:5173"]

    # Storage de planos (Sprint 2)
    storage_root: str = "/var/lib/heatmapper/planos"
    storage_url_secret: str = "cambia_esto_secreto_para_firmar_urls"
    storage_url_ttl_seconds: int = 3600  # 1 hora
    # Prefijo opcional para URLs firmadas (e.g. "http://host/api"). Si vacío
    # se devuelven URLs relativas que el cliente concatena con su base.
    public_api_url: str = ""

    # Firebase Admin SDK (notificaciones de asignación de proyectos)
    firebase_project_id: str = ""
    firebase_credentials_path: str = ""
    firebase_credentials_json: str = ""


settings = Settings()
