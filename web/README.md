# Wireless HeatMapper — Panel Web (React + TypeScript)

Panel de administración y portal de cliente para el sistema de cobertura WiFi.  
Stack: React 19 + TypeScript + Vite + TanStack Query + Axios + Zustand.

## Requisitos

- Node.js ≥ 22
- Backend levantado (ver [README raiz](../README.md))

## Configuración rápida

```bash
# Instalar dependencias
npm install

# Servidor de desarrollo (http://localhost:5173)
npm run dev

# Verificar tipos TypeScript
npx tsc --noEmit

# Lint ESLint
npm run lint

# Build de producción
npm run build

# Preview del build
npm run preview
```

## Estructura

```
src/
  api/           # Clientes Axios por recurso
  components/    # Componentes reutilizables
  features/      # Módulos por funcionalidad (auth, proyectos, heatmap...)
  hooks/         # Custom hooks (TanStack Query)
  pages/         # Vistas principales (ruteadas)
  store/         # Estado global Zustand
  types/         # Tipos TypeScript compartidos
```

## Variables de entorno

Crear un archivo `.env.local` en `web/`:

```env
VITE_API_BASE_URL=http://localhost/api
```

En producción el Nginx reverse proxy enruta `/api` al backend automáticamente.

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(["dist"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ["./tsconfig.node.json", "./tsconfig.app.json"],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
]);
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from "eslint-plugin-react-x";
import reactDom from "eslint-plugin-react-dom";

export default defineConfig([
  globalIgnores(["dist"]),
  {
    files: ["**/*.{ts,tsx}"],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs["recommended-typescript"],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ["./tsconfig.node.json", "./tsconfig.app.json"],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
]);
```
