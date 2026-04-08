# Stock Control - Frontend SPA (Vue 3 + Vite)

Este es el cliente moderno Single Page Application (SPA) para el sistema de control de stock de Grupo Hernandez.

## Stack Tecnologico
- **Core**: Vue 3 (Composition API)
- **Estado**: Pinia (Stores de dominio desacopladas)
- **Rutas**: Vue Router (Lazy loading habilitado)
- **Estilos**: Tailwind CSS (Sistema de diseño institucional Navy/Amber)
- **Transporte**: Axios (API Client centralizado)

## Estructura de Proyecto
- `src/api/`: Modulos de comunicacion con FastAPI.
- `src/stores/`: Logica de estado persistente y reactivo por dominio.
- `src/views/`: Pantallas principales organizadas por modulo (catalog, orders, dispatch, etc.).
- `src/components/`: Componentes reutilizables (UI, Layout, Common).
- `src/utils/`: Formateadores, normalizadores y sesion de usuario.

## Comandos Disponibles
```bash
# Instalar dependencias
npm install

# Desarrollo local con HMR
npm run dev

# Compilar para produccion (Carpeta /dist)
npm run build

# Previsualizar el build de produccion
npm run preview
```

## Convenciones Criticas
1. **Mutaciones**: Usar siempre el flag `isSubmitting` para controlar estados de carga en botones y formularios.
2. **Normalizacion**: Los datos provenientes del backend deben pasar por `src/utils/normalizers.js` antes de ser consumidos en las vistas.
3. **Seguridad**: Las rutas están protegidas mediante guardias en `src/router/index.js` basados en el rol del usuario (`admin`, `manager`, `superadmin`).
