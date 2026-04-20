# F.I.C.C.T. Proyecto Final SW2

Base de trabajo pensada como monorepo para frontend mobile/web y backend.

## Descripcion del proyecto

Wireless HeatMapper es una herramienta movil para el analisis y optimizacion
de cobertura WiFi mediante mapas de calor. La idea central del proyecto es
capturar mediciones reales de redes inalambricas dentro de un ambiente,
ubicarlas sobre un plano y, en etapas posteriores, transformar esos datos en
visualizaciones, analisis de cobertura y sugerencias de posicionamiento de
puntos de acceso.

La validacion tecnica mas importante del proyecto no es el heatmap, sino la
captura correcta de mediciones reales sobre un plano. Por eso el primer sprint
se enfoca en levantar datos confiables desde Android.

## Estructura actual

- `apps/mobile`: aplicacion Flutter creada y lista para evolucionar.
- `apps/web`: base inicial del frontend web en `Next.js`.
- `frontend`: dashboard legacy basado en `Bootstrap 4`, usado como referencia
  visual para la migracion a `Next.js`.

## Estructura recomendada a futuro

- `apps/mobile`: Flutter para Android y Web.
- `apps/web`: frontend web con Next.js.
- `apps/api`: backend con NestJS.

## Versiones actuales

- `Flutter`: `3.41.7`
- `Dart`: `3.11.5`
- `DevTools`: `2.54.2`
- `Version de la app`: `1.0.0+1`
- `SDK constraint`: `^3.11.5`

## Sprint 1

### Objetivo

Lograr que la app ya sirva para capturar datos reales de cobertura WiFi dentro
de un ambiente.

### Alcance funcional

El Sprint 1 debe incluir:

- carga de plano o imagen del ambiente
- seleccion manual de puntos sobre el plano
- escaneo WiFi desde Android
- registro por punto de:
  - coordenada `x`
  - coordenada `y`
  - `SSID`
  - `BSSID`
  - `RSSI`
  - `frecuencia`
  - `canal` cuando sea posible
- guardado local de mediciones

### Entregable esperado

Una app donde el usuario pueda:

- abrir un plano o imagen
- tocar un punto dentro del plano
- realizar una medicion WiFi real
- guardar esa medicion localmente

### Por que este sprint es el mas importante

Este sprint valida el corazon del proyecto:

- que Flutter puede manejar plano + interaccion visual
- que Android permite capturar datos WiFi utiles para el caso real
- que las mediciones pueden asociarse a coordenadas dentro del ambiente
- que ya existe una base de datos real sobre la cual luego se podran construir
  heatmaps, analisis y sugerencias inteligentes

Sin este sprint funcionando, el resto del proyecto seria solo una simulacion o
una capa visual sin datos confiables.

### Modelo de datos minimo

Para que la base sea compatible a futuro con `NestJS` y `Next.js`, conviene
trabajar desde ya con estas entidades:

`FloorPlan`
- `id`
- `name`
- `imagePath`
- `width`
- `height`
- `createdAt`

`MeasurementPoint`
- `id`
- `floorPlanId`
- `x`
- `y`
- `label` opcional
- `createdAt`

`WifiReading`
- `id`
- `measurementPointId`
- `ssid`
- `bssid`
- `rssi`
- `frequency`
- `channel`
- `timestamp`

### Criterios de aceptacion

- el usuario puede seleccionar una imagen del plano desde el dispositivo
- la imagen se muestra correctamente en pantalla
- el usuario puede tocar un punto y registrar coordenadas relativas al plano
- la app puede escanear redes WiFi reales en Android
- por cada punto se guarda al menos una lectura con `SSID`, `BSSID`, `RSSI` y
  `frequency`
- las mediciones quedan persistidas localmente
- al volver a abrir la app, los datos siguen disponibles

### Orden recomendado de implementacion

1. carga y visualizacion del plano
2. seleccion de puntos sobre la imagen
3. persistencia local de planos y puntos
4. escaneo WiFi en Android
5. asociacion de lecturas WiFi con cada punto
6. listado o marcado visual de mediciones guardadas

### Lo que no entra todavia

Estas partes quedan para sprints posteriores:

- generacion de heatmap
- interpolacion espacial
- analisis de cobertura
- deteccion de interferencias
- sugerencias automaticas de posicionamiento
- IA
- sincronizacion con backend
- reportes avanzados

### Riesgos tecnicos a considerar

- el escaneo WiFi depende de permisos de Android y, normalmente, permisos de
  ubicacion
- algunos dispositivos limitan la frecuencia de escaneo
- no todos los telefonos exponen exactamente la misma informacion
- el `canal` puede requerir derivarse desde `frequency`
- para este sprint conviene trabajar primero con imagenes `PNG` o `JPG` en vez
  de `PDF`

### Arquitectura recomendada en Flutter

Dentro de `apps/mobile/lib/src`, la organizacion recomendada es:

- `core/`
- `features/floor_plan/`
- `features/measurement/`
- `features/wifi_scan/`
- `data/local/`

Esto deja la app lista para crecer ordenadamente y facilita mapear luego las
entidades y flujos hacia una API en `NestJS` y un frontend web en `Next.js`.

## Ejecutar Flutter

```bash
cd apps/mobile
/tmp/flutter-sdk/bin/flutter pub get
/tmp/flutter-sdk/bin/flutter run
```

## Ejecutar Next.js

```bash
cd apps/web
npm install
npm run dev
```

## Ejecutar Next.js con Docker

```bash
cd apps/web
docker compose up --build
```

## Ejecutar en Android fisico

### Ver dispositivos disponibles

```bash
adb devices -l
/tmp/flutter-sdk/bin/flutter devices
```

### Ejecutar por USB

Si el telefono ya esta conectado por cable y visible en `flutter devices`:

```bash
cd apps/mobile
/tmp/flutter-sdk/bin/flutter run -d R5CN90TGVTK
```

### Ejecutar por WiFi

Primero conecta el telefono por USB y habilita `adb` por red:

```bash
adb tcpip 5555
adb connect 192.168.26.13:5555
```

Luego verifica que aparezca como dispositivo remoto:

```bash
adb devices -l
/tmp/flutter-sdk/bin/flutter devices
```

Finalmente ejecuta la app por WiFi:

```bash
cd apps/mobile
/tmp/flutter-sdk/bin/flutter run -d 192.168.26.13:5555
```

### Si la conexion WiFi se cae

Vuelve a conectar el dispositivo con:

```bash
adb connect 192.168.26.13:5555
```

## Configurar la URL del backend

Puedes pasar variables de compilacion con `--dart-define`:

```bash
cd apps/mobile
/tmp/flutter-sdk/bin/flutter run \
  --dart-define=APP_ENV=development \
  --dart-define=API_BASE_URL=http://localhost:3000/api
```

## Siguiente paso sugerido

Crear primero el backend en `NestJS` con rutas claras como `/auth`, `/users` o
`/products`, y luego conectar Flutter a esas rutas desde una capa de servicios.
