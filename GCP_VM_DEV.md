# Desarrollo En GCP VM

Guía pensada para trabajar por SSH en una VM de Google Cloud con hot reload de backend y web, sin exponer el stack de desarrollo públicamente.

## Objetivo

- Backend FastAPI con `--reload`
- Frontend Vite con HMR
- Acceso desde tu máquina local mediante túnel SSH
- Puertos ligados a `127.0.0.1` dentro de la VM por defecto

## 1. Preparar la VM

Instalar Docker Engine y Docker Compose Plugin en la VM.

Clonar el repositorio y crear el archivo de entorno:

```bash
cp .env.example .env
```

Editar al menos:

```env
POSTGRES_PASSWORD=una_clave_segura
SECRET_KEY=una_clave_larga_y_segura
```

Configuración sugerida para exponer el stack usando los puertos libres `5435`, `3000` y `8081`:

```env
DB_BIND_HOST=127.0.0.1
DB_HOST_PORT=5435
NGINX_BIND_HOST=0.0.0.0
NGINX_HOST_PORT=8081
BACKEND_BIND_HOST=0.0.0.0
BACKEND_HOST_PORT=3000
```

## 2. Levantar el stack

```bash
docker compose up --build -d
```

Seguir logs:

```bash
docker compose logs -f backend web nginx
```

Verificar salud:

```bash
curl http://localhost:8081/api/health
curl http://localhost:3000/health
```

## 3. Conectarte desde tu máquina local o móvil

Con esa configuración, el acceso directo queda así:

```bash
http://34.67.188.26:8081
```

Usar:

- Web: `http://34.67.188.26:8081`
- API proxied: `http://34.67.188.26:8081/api`
- Backend directo: `http://34.67.188.26:3000`
- OpenAPI: `http://34.67.188.26:8081/api/docs`

## 4. Flujo diario

El código fuente queda montado dentro de los contenedores:

- Cambios en `backend/` recargan FastAPI automáticamente.
- Cambios en `web/` actualizan Vite con HMR.

Comandos útiles:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f web
docker compose restart backend
docker compose restart web
docker compose down
```

## 5. App móvil contra la VM

### Emulador Android o dispositivo físico

Si vas a conectar la app directamente a la VM, usar:

```bash
flutter run --dart-define=API_BASE_URL=http://34.67.188.26:8081/api
```

## 6. Notas

- Esta configuración es para desarrollo remoto, no para producción.
- El override de Compose activa `DEBUG=true`, `seed_dev` y `uvicorn --reload`.
- Si en algún momento quieres exponer el servicio más allá de localhost de la VM, cambia explícitamente `NGINX_BIND_HOST` y `BACKEND_BIND_HOST`.
