# MDScope

MDScope es una app TUI para leer documentación técnica en Markdown desde terminal, con exploración de proyecto, preview renderizado, TOC lateral, búsqueda y una ruta clara para soportar Mermaid, charts e imágenes inline con degradación elegante.

La documentación inicial del proyecto está en [`docs/README.md`](docs/README.md).

## Estado actual

El proyecto ya soporta:

- explorador de archivos Markdown,
- preview renderizado en terminal,
- TOC navegable,
- búsqueda local con SQLite FTS5,
- hot reload con `watchdog`,
- render Mermaid opcional via `mmdc`,
- fallback para charts e imágenes.

## Uso

Desde el repo del proyecto:

```bash
uv run mdscope .
uv run mdscope README.md
uv run mdscope /ruta/a/otro/proyecto
```

Desde cualquier carpeta, apuntando al repo donde vive el comando:

```bash
uv run --directory /home/elyarestark/develop/MDScope mdscope .
uv run --directory /home/elyarestark/develop/MDScope mdscope /ruta/a/docs
```

Si quieres instalarlo como herramienta y usarlo globalmente:

```bash
uv tool install --from /home/elyarestark/develop/MDScope MDScope
```

Despues de eso deberias poder usar cualquiera de estos comandos desde otras carpetas:

```bash
MDScope .
MDScope README.md
mdscope .
mdscope README.md
```

Si actualizas el repo y quieres reinstalar la version global:

```bash
uv tool install --reinstall --from /home/elyarestark/develop/MDScope MDScope
```

## Mermaid opcional

Si quieres render Mermaid real, instala Mermaid CLI:

```bash
npm install -g @mermaid-js/mermaid-cli
```

Si ademas tienes `chafa`, MDScope puede mostrar el diagrama generado directamente en terminal. Sin `mmdc`, los bloques Mermaid siguen degradando a un fallback legible.

## Charts opcionales

Si quieres render real para bloques `chart`, instala las dependencias de charts:

```bash
uv sync --extra charts
```

Formato inicial soportado:

````md
```chart
title: Requests
type: line
x: 1,2,3,4
y: 12,18,9,22
xlabel: Dia
ylabel: Total
```
````

Tipos soportados por ahora:
- `line`
- `bar`

## Atajos actuales

- `/`: enfocar búsqueda
- `Tab`: siguiente panel
- `Shift+Tab`: panel anterior
- `r`: refrescar documento/proyecto
- `f`: volver al documento completo
- `Esc`: limpiar búsqueda
- `q`: salir

## Desarrollo

```bash
uv run --extra dev pytest
uv run --extra dev ruff check .
uv run --extra dev mypy src tests
```

## Documentación

- [`docs/README.md`](docs/README.md): visión general, stack recomendado, MVP y roadmap.
- [`docs/implementation-plan.md`](docs/implementation-plan.md): plan de acción por fases, arquitectura y tareas concretas.
- [`docs/phases.md`](docs/phases.md): checklist operativo de fases para implementar una por una.
- [`docs/post-mvp-phases.md`](docs/post-mvp-phases.md): roadmap de evolución despues del plan base, incluyendo instalacion global, Mermaid real, charts, packaging y UX.
