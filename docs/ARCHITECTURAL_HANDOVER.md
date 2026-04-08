# Architectural Handover - Frontend SPA

## Resumen de la Intervencion
El frontend ha sido migrado de un modelo hibrido Flask/Jinja a una SPA pura en Vue 3, desacoplando completamente la logica de negocio del servidor de plantillas y preparándolo para una paridad futura con aplicaciones moviles.

## Pilares de la Nueva Arquitectura

### 1. Desacoplamiento de Stores (Domain Driven)
Se elimino la `catalogStore` monolitica en favor de stores especificas por dominio:
- `productStore`: Gestion de items y sincronizacion.
- `userStore`: Gestion de administradores y usuarios.
- `buildingStore`: Gestion de sedes y asignaciones.

### 2. Contratos y Normalizacion
Se introdujo una capa de normalizacion (`src/utils/normalizers.js`) que garantiza que los objetos del backend sigan un esquema predecible en el frontend, permitiendo cambios en la API sin romper las vistas masivamente.

### 3. Resiliencia de UX
- **Skeletons**: Implementacion de `DashboardSkeleton` para transiciones suaves.
- **Loading States**: Uso estandarizado de `isLoading` y `isSubmitting`.
- **Empty States**: Manejo explicito de listas vacias y errores de red.

## Riesgos Residuales Conocidos
- **Filtrado Extensivo**: El filtrado de busqueda en el catalogo es reactivo por parte del cliente. En catalogos >1000 items, se recomienda mover el filtrado al backend.
- **Tokens de Larga Duracion**: La sesion actual persiste en `localStorage`. Se debe monitorear el refresco de tokens en implementaciones futuras.

## Proximos Pasos Recomendados
1.  **Refactor de Componetizacion**: Extraer la logica de filtrado de `MyOrdersView.vue` a un composable dedicado.
2.  **QA Automatizado**: Introducir tests E2E con Playwright o Cypress para los flujos de Ordenes y Despacho.
