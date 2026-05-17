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
curl http://localhost:8081/api/health
# Respuesta esperada: {"status":"ok","version":"0.1.0","db":"ok"}
```

> Por defecto, los puertos de desarrollo quedan ligados a `127.0.0.1`.
> Esto evita exponer accidentalmente el stack cuando trabajas en una VM remota.

Servicios disponibles tras `docker compose up`:

| Servicio              | URL                       |
| --------------------- | ------------------------- |
| Panel web (React)     | http://localhost:8081     |
| API REST (FastAPI)    | http://localhost:8081/api |
| API REST directa      | http://localhost:3000     |
| Documentación OpenAPI | http://localhost:8081/api/docs |

---

## Desarrollo en GCP VM por SSH

Flujo recomendado:

```bash
# En la VM
cp .env.example .env
# Editar SECRET_KEY y POSTGRES_PASSWORD
docker compose up --build -d
docker compose logs -f backend web nginx
```

Desde tu máquina local, abrir un túnel SSH:

```bash
ssh -L 8081:127.0.0.1:8081 -L 3000:127.0.0.1:3000 <usuario>@<IP_VM>
```

URLs desde tu máquina local con el túnel activo:

| Servicio                  | URL local               |
| ------------------------- | ----------------------- |
| Panel web                 | http://localhost:8081   |
| API proxied por Nginx     | http://localhost:8081/api |
| Backend directo           | http://localhost:3000   |
| OpenAPI                   | http://localhost:8081/api/docs |

Para un emulador Android ejecutándose en tu máquina local contra la VM remota:

```bash
flutter run --dart-define=API_BASE_URL=http://34.67.188.26:8081/api
```

Guía rápida ampliada: [GCP_VM_DEV.md](GCP_VM_DEV.md).

---

## Desarrollo local por componente

### Backend (FastAPI + PostgreSQL)

```bash
cd backend
pip install -e ".[dev]"

# Aplicar migraciones
DATABASE_URL=postgresql://... alembic upgrade head

# Ejecutar servidor con recarga automática
uvicorn app.main:app --reload --port 3000
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
