# Wireless HeatMapper

Sistema integrado de relevamiento y análisis de cobertura WiFi.
**Cliente:** Bulldog Tech. | **Equipo:** FICCT-UAGRM Grupo 24 | **Modalidad:** 100 % en línea

---

## Requisitos previos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) ≥ 24 con Compose v2
- [Flutter SDK](https://flutter.dev/docs/get-started/install) ≥ 3.6 (para desarrollo móvil)
- [Node.js](https://nodejs.org/) ≥ 22 (para desarrollo web local sin Docker)
- [Python](https://www.python.org/) ≥ 3.11 (para desarrollo backend local sin Docker)

---

## Ejecución completa con Docker Compose

```bash
# 1. Copiar variables de entorno
cp .env.example .env
# Editar .env con valores reales (al menos SECRET_KEY y POSTGRES_PASSWORD)

# 2. Levantar todos los servicios (db + backend + web + nginx)
docker compose up --build

# 3. Verificar que el backend está operativo
curl http://localhost/api/health
# Respuesta esperada: {"status":"ok","version":"0.1.0","db":"ok"}
```

Servicios disponibles tras `docker compose up`:

| Servicio              | URL                       |
| --------------------- | ------------------------- |
| Panel web (React)     | http://localhost          |
| API REST (FastAPI)    | http://localhost/api      |
| Documentación OpenAPI | http://localhost/api/docs |

Si levantas con el override local `docker-compose.local.yml`, el proxy Nginx se publica en `http://localhost:8081` y el backend directo en `http://localhost:8001` para evitar conflicto con puertos `80`, `8080` y `8000` ya ocupados en esta VM.

---

## Desarrollo local por componente

### Backend (FastAPI + PostgreSQL)

```bash
cd backend
pip install -e ".[dev]"

# Aplicar migraciones
DATABASE_URL=postgresql://... alembic upgrade head

# Ejecutar servidor con recarga automática
uvicorn app.main:app --reload --port 8000
```

Ver guía completa en [backend/README.md](backend/README.md).

### Web (React + TypeScript + Vite)

```bash
cd web
npm install
npm run dev        # Servidor de desarrollo en http://localhost:5173
npm run build      # Build de producción
npm run lint       # Verificar ESLint
```

Ver guía completa en [web/README.md](web/README.md).

### App móvil (Flutter / Android)

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
flutter run        # Requiere emulador o dispositivo conectado
```

> La app se conecta a `http://10.0.2.2/api` por defecto (emulador Android apunta al localhost del host).
> Para un dispositivo físico configurar `API_BASE_URL` en el build:
> `flutter run --dart-define=API_BASE_URL=http://<IP_LOCAL>/api`

Ver guía completa en [mobile/README.md](mobile/README.md).

---

## Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

Los hooks aplican automáticamente `ruff`, `prettier` y `eslint` antes de cada commit.
