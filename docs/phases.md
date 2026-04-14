# Fases de implementación de MDScope

Este documento concentra todas las fases del proyecto en un solo lugar para usarlas como plan operativo. La idea es cerrar cada fase por completo antes de pasar a la siguiente.

## Fase 1: Bootstrap del proyecto

### Objetivo

Dejar el repositorio listo para desarrollo, instalación y ejecución local.

### Alcance

- inicializar proyecto Python 3.12+,
- configurar `uv`,
- definir `pyproject.toml`,
- crear estructura `src/`,
- crear entrypoint `mdscope`,
- configurar tooling base.

### Entregables

- `pyproject.toml`,
- paquete `src/mdscope/`,
- comando `mdscope --help`,
- configuración de `ruff`,
- configuración de `pytest`,
- configuración base de `mypy`,
- `README.md` y `docs/` alineados con el estado real del repo.

### Tareas

1. Crear estructura base del paquete.
2. Declarar dependencias núcleo:
   - `typer`
   - `textual`
   - `rich`
   - `markdown-it-py`
   - `watchdog`
3. Declarar dependencias de desarrollo:
   - `pytest`
   - `pytest-asyncio`
   - `ruff`
   - `mypy`
4. Configurar script ejecutable `mdscope`.
5. Añadir prueba mínima de import o smoke test.

### Criterio de cierre

- `uv run mdscope --help` funciona.
- `pytest` corre al menos una prueba básica.
- `ruff check` corre sobre el repositorio.

## Fase 2: CLI mínima y arranque TUI

### Objetivo

Levantar una app TUI funcional, aunque todavía simple.

### Alcance

- aceptar un path de archivo o directorio,
- validar entrada,
- lanzar una app `Textual` mínima,
- mostrar layout base de tres paneles.

### Entregables

- CLI con argumentos iniciales,
- `Textual App` mínima,
- panel de explorador,
- panel principal de preview,
- panel lateral para TOC o detalles.

### Tareas

1. Implementar `src/mdscope/cli/app.py`.
2. Implementar `src/mdscope/ui/app.py`.
3. Crear layout inicial de tres paneles.
4. Pasar el path resuelto desde CLI hacia la app.
5. Mostrar estado inicial cuando no haya documento cargado.

### Criterio de cierre

- `mdscope .` abre la TUI.
- `mdscope README.md` abre la TUI con el path recibido.

## Fase 3: Descubrimiento de archivos Markdown

### Objetivo

Poder explorar documentación dentro de un proyecto.

### Alcance

- detectar archivos `.md`,
- construir árbol de navegación,
- soportar apertura desde archivo o directorio,
- resolver documento inicial.

### Entregables

- `project_loader.py`,
- modelo de nodos del proyecto,
- lista o árbol navegable de archivos Markdown.

### Tareas

1. Implementar descubrimiento basado en `pathlib`.
2. Ignorar archivos no Markdown.
3. Resolver directorio raíz del proyecto activo.
4. Seleccionar un documento inicial válido.
5. Conectar árbol de archivos con la UI.

### Criterio de cierre

- la barra lateral muestra documentos Markdown del proyecto,
- seleccionar un archivo cambia el documento activo.

## Fase 4: Parser estructural de Markdown

### Objetivo

Interpretar el documento con suficiente estructura para render y navegación.

### Alcance

- parsear headings,
- detectar bloques,
- detectar fences de código,
- preparar base para bloques especiales.

### Entregables

- `markdown_parser.py`,
- modelos `Document`, `Heading`, `RenderBlock`,
- extracción de TOC.

### Tareas

1. Integrar `markdown-it-py`.
2. Extraer headings con nivel, texto y ancla.
3. Identificar bloques de código.
4. Detectar tablas y listas como estructura útil.
5. Preparar clasificación de fences especiales:
   - `mermaid`
   - `chart`

### Criterio de cierre

- abrir un `.md` produce una estructura parseada reusable,
- la TOC refleja correctamente los headings del documento.

## Fase 5: Render de Markdown en terminal

### Objetivo

Mostrar el contenido de forma legible y útil dentro de la TUI.

### Alcance

- render de Markdown común,
- resaltado de código,
- tablas y links,
- sincronización con la TOC.

### Entregables

- `markdown_renderer.py`,
- `code_renderer.py`,
- preview central funcional.

### Tareas

1. Conectar parser con render.
2. Renderizar headings, párrafos, listas y tablas.
3. Renderizar fences con syntax highlighting usando `Rich`.
4. Manejar links sin romper el layout.
5. Actualizar panel TOC al cambiar documento.

### Criterio de cierre

- un documento técnico típico se puede leer bien desde la TUI,
- los bloques de código conservan estructura y color.

## Fase 6: Navegación y experiencia de lectura

### Objetivo

Hacer la aplicación utilizable sin fricción desde teclado.

### Alcance

- navegación entre paneles,
- navegación entre archivos,
- navegación por headings,
- comandos de refresco y foco.

### Entregables

- keybindings base,
- selección de secciones desde TOC,
- mejor estado de foco visual.

### Tareas

1. Definir keybindings mínimos.
2. Cambiar foco entre explorador, preview y TOC.
3. Permitir abrir archivo desde el panel lateral.
4. Permitir saltar a heading desde TOC.
5. Añadir barra de estado o ayuda mínima.

### Criterio de cierre

- se puede usar la app completamente con teclado,
- el flujo de lectura es claro y estable.

## Fase 7: Búsqueda local con SQLite FTS5

### Objetivo

Buscar contenido de forma rápida a nivel proyecto.

### Alcance

- indexación inicial,
- búsqueda por término,
- resultados navegables,
- apertura de documento desde resultado.

### Entregables

- `search_index.py`,
- base SQLite local,
- UI de búsqueda.

### Tareas

1. Diseñar esquema de indexación.
2. Crear tabla FTS5.
3. Indexar path, título, headings y contenido.
4. Implementar consulta y ranking básico.
5. Añadir pantalla o panel de resultados.

### Criterio de cierre

- `mdscope` encuentra resultados relevantes dentro del proyecto,
- abrir un resultado posiciona correctamente el documento.

## Fase 8: Hot reload

### Objetivo

Reflejar cambios del sistema de archivos sin reiniciar la app.

### Alcance

- observar archivo abierto,
- observar cambios del proyecto,
- refrescar documento e índice.

### Entregables

- `file_watcher.py`,
- actualización del preview,
- reindexado incremental básico.

### Tareas

1. Integrar `watchdog`.
2. Detectar cambios sobre archivos `.md`.
3. Debounce de eventos.
4. Refrescar documento abierto al modificarse.
5. Actualizar índice de búsqueda al cambiar contenido.

### Criterio de cierre

- editar un documento abierto actualiza la vista,
- los resultados de búsqueda reflejan cambios recientes.

## Fase 9: Soporte opcional para bloques especiales

### Objetivo

Añadir valor visual sin convertirlo en dependencia obligatoria del lector.

### Alcance

- Mermaid opcional,
- charts terminal,
- detección de capacidades,
- degradación elegante.

### Entregables

- `mermaid_renderer.py`,
- `chart_renderer.py`,
- `capabilities.py`,
- adaptadores externos desacoplados.

### Tareas

1. Detectar bloques `mermaid` y `chart`.
2. Integrar Mermaid CLI como adaptador opcional.
3. Integrar `plotext` o `textual-plotext`.
4. Detectar soporte de terminal.
5. Implementar fallback textual si la capacidad no existe.

### Criterio de cierre

- los bloques especiales se renderizan cuando es posible,
- cuando no, la app sigue siendo completamente usable.

## Fase 10: Imágenes inline y fallback visual

### Objetivo

Extender la experiencia visual en terminales compatibles.

### Alcance

- soporte Kitty graphics,
- fallback con `chafa`,
- control por capacidades detectadas.

### Entregables

- `kitty_adapter.py`,
- `chafa_adapter.py`,
- `image_renderer.py`.

### Tareas

1. Detectar terminal compatible con Kitty graphics.
2. Renderizar imágenes cuando el protocolo esté disponible.
3. Integrar `chafa` como fallback portable.
4. Añadir política clara de activación y fallback.

### Criterio de cierre

- el mismo documento puede mostrar imagen enriquecida o fallback útil según el terminal.

## Fase 11: Endurecimiento, pruebas y pulido

### Objetivo

Cerrar la brecha entre prototipo y herramienta de uso diario.

### Alcance

- pruebas de dominio y UI,
- manejo de errores,
- rendimiento básico,
- documentación final de uso y desarrollo.

### Entregables

- tests del parser,
- tests de búsqueda,
- tests async de flujos TUI,
- políticas de error claras,
- documentación de usuario.

### Tareas

1. Añadir tests para parsing, indexado y watchers.
2. Añadir smoke tests de la app TUI.
3. Medir tiempos básicos de carga e indexación.
4. Endurecer errores de IO y dependencias faltantes.
5. Completar guía de uso y desarrollo.

### Criterio de cierre

- el proyecto es estable, instalable y mantenible sobre repositorios reales.

## Orden de ejecución recomendado

1. Fase 1
2. Fase 2
3. Fase 3
4. Fase 4
5. Fase 5
6. Fase 6
7. Fase 7
8. Fase 8
9. Fase 9
10. Fase 10
11. Fase 11

## Regla de trabajo

No avanzar a la siguiente fase hasta cerrar:

- código,
- verificación mínima,
- documentación impactada,
- y criterio de cierre de la fase actual.
