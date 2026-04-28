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

Los puertos de desarrollo quedan ligados a localhost de la VM por defecto:

```env
NGINX_BIND_HOST=127.0.0.1
NGINX_HOST_PORT=80
BACKEND_BIND_HOST=127.0.0.1
BACKEND_HOST_PORT=8000
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
curl http://localhost/api/health
curl http://localhost:8000/health
```

## 3. Conectarte desde tu máquina local

Abrir un túnel SSH:

```bash
ssh -L 8080:127.0.0.1:80 -L 8000:127.0.0.1:8000 <usuario>@<IP_VM>
```

Con el túnel activo, usar:

- Web: `http://localhost:8080`
- API proxied: `http://localhost:8080/api`
- Backend directo: `http://localhost:8000`
- OpenAPI: `http://localhost:8080/api/docs`

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

### Emulador Android en tu máquina local

Si el túnel SSH expone la web/API en tu máquina local por el puerto `8080`, ejecutar:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080/api
```

`10.0.2.2` es el alias del host para el emulador Android.

### Dispositivo físico

El túnel SSH no suele ser práctico para un teléfono físico. En ese caso necesitas una URL accesible desde el dispositivo, idealmente `https://<dominio>/api`.

## 6. Notas

- Esta configuración es para desarrollo remoto, no para producción.
- El override de Compose activa `DEBUG=true`, `seed_dev` y `uvicorn --reload`.
- Si en algún momento quieres exponer el servicio más allá de localhost de la VM, cambia explícitamente `NGINX_BIND_HOST` y `BACKEND_BIND_HOST`.
