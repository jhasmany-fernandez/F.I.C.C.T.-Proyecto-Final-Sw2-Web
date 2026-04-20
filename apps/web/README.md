# Wireless HeatMapper Web

Base inicial en `Next.js` para reutilizar la interfaz del dashboard ubicado en [../../frontend](../../frontend), pero adaptada al dominio del proyecto.

## Incluye

- layout con sidebar, header y dashboard responsivo
- rutas base para `planos`, `mediciones`, `escaneos`, `reportes` y `configuracion`
- estilos inspirados en la interfaz actual sin tocar la carpeta `frontend`
- datos mock listos para reemplazar por una API o capa local

## Ejecutar

```bash
cd apps/web
npm install
npm run dev
```

La app quedara disponible en `http://localhost:3333`.

## Ejecutar con Docker

Modo desarrollo con hot reload:

```bash
cd apps/web
docker compose up --build
```

Con esto el codigo queda montado dentro del contenedor y los cambios del frontend
se reflejan sin reconstruir la imagen en cada edicion.

Modo produccion:

```bash
cd apps/web
docker compose -f compose.prod.yaml up --build
```

La app quedara disponible en `http://localhost:3333`.

## Siguiente paso recomendado

Conectar estas vistas a entidades reales como `FloorPlan`, `MeasurementPoint` y `WifiReading`, compartiendo contratos con el backend cuando exista `apps/api`.
