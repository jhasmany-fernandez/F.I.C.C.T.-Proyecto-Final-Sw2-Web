# Wireless HeatMapper — Backend (FastAPI + PostgreSQL)

API REST + módulo IA para el sistema de cobertura WiFi.  
Stack: Python 3.12 + FastAPI + SQLAlchemy + Alembic + PostgreSQL 15.

## Requisitos

- Python ≥ 3.11
- PostgreSQL 15 (o Docker Compose para el entorno completo)

## Configuración rápida

```bash
# Instalar dependencias (incluye dev: pytest, ruff, httpx)
pip install -e ".[dev]"

# Copiar y configurar variables de entorno
cp ../.env.example ../.env

# Aplicar migraciones
DATABASE_URL=postgresql://<user>:<pw>@localhost:5432/heatmapper alembic upgrade head

# Servidor con recarga automática
uvicorn app.main:app --reload --port 8000
```

## Verificación

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0","db":"ok"}
```

## Pruebas

```bash
# Las pruebas de CI usan SQLite (sin PostgreSQL)
DATABASE_URL=sqlite:///./test.db pytest tests/ -v
```

## Lint

```bash
ruff check .
ruff format .
```

## Estructura

```
app/
  api/          # Routers FastAPI (v1/)
  core/         # Config, database (SQLAlchemy engine), seguridad JWT
  models/       # Modelos ORM (SQLAlchemy declarativo)
  schemas/      # DTOs Pydantic (entrada/salida)
  repositories/ # Acceso a datos (consultas SQLAlchemy)
  services/     # Lógica de aplicación / casos de uso
  ai/           # Módulo IA (Sprint 5+)
alembic/
  versions/     # Migraciones versionadas
tests/
```

## Variables de entorno

| Variable                      | Por defecto                                                | Descripción                   |
| ----------------------------- | ---------------------------------------------------------- | ----------------------------- |
| `DATABASE_URL`                | `postgresql://heatmapper_user:password@db:5432/heatmapper` | Cadena de conexión SQLAlchemy |
| `SECRET_KEY`                  | `cambia_esto_por_un_secreto_seguro`                        | Clave JWT                     |
| `ALGORITHM`                   | `HS256`                                                    | Algoritmo JWT                 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                                                       | Expiración del token          |
| `DEBUG`                       | `false`                                                    | Modo debug                    |
| `CORS_ORIGINS`                | `["http://localhost","http://localhost:5173"]`             | Orígenes CORS permitidos      |
