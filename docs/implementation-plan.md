# Plan de implementación de MDScope

## Resultado esperado

Construir una TUI estable para lectura de Markdown técnico en terminal con:

- explorador de proyecto,
- preview renderizado,
- tabla de contenidos lateral,
- búsqueda local,
- hot reload,
- y una arquitectura preparada para Mermaid, charts e imágenes inline sin convertir esas integraciones en dependencia obligatoria del núcleo.

## Fases de ejecución

## Fase 0: Bootstrap del repositorio

### Objetivo

Dejar una base mantenible y lista para iterar.

### Entregables

- `pyproject.toml` con dependencias base y extras opcionales.
- estructura `src/` y `tests/`,
- comando `mdscope`,
- configuración de `ruff`, `pytest` y `mypy`,
- `README.md` y docs iniciales.

### Tareas

1. Inicializar proyecto con `uv`.
2. Configurar paquete `src/mdscope`.
3. Añadir `Typer`, `Textual`, `Rich`, `markdown-it-py`, `watchdog`.
4. Preparar grupos de dependencias opcionales:
   - `dev`
   - `charts`
   - `mermaid`
   - `images`
5. Definir `console_scripts` o entrypoint equivalente para `mdscope`.
6. Crear suite mínima de pruebas y CI local básica.

### Criterio de cierre

`mdscope --help` funciona y el proyecto puede instalarse y ejecutar tests básicos.

## Fase 1: Núcleo de lectura

### Objetivo

Entregar una experiencia útil de lectura y navegación sobre Markdown.

### Entregables

- apertura de archivo o directorio,
- árbol de documentos Markdown,
- panel de preview,
- TOC lateral,
- navegación por teclado,
- render legible de headings, listas, tablas, links y código.

### Tareas

1. Implementar parsing de entrada CLI:
   - `mdscope .`
   - `mdscope README.md`
   - `mdscope docs/`
   - `mdscope README.md --section "Arquitectura"`
2. Crear modelos base:
   - `Document`
   - `Heading`
   - `ProjectNode`
   - `RenderBlock`
3. Implementar `project_loader.py` para descubrir archivos `.md`.
4. Implementar `markdown_parser.py` con `markdown-it-py` para:
   - extraer headings,
   - identificar fences,
   - separar bloques especiales.
5. Implementar `markdown_renderer.py` con `Rich`.
6. Construir layout principal en `Textual`:
   - sidebar de archivos,
   - preview central,
   - TOC lateral.
7. Definir keybindings mínimos:
   - moverse entre paneles,
   - abrir archivo,
   - saltar a heading,
   - refrescar.

### Criterio de cierre

Un usuario puede abrir un repositorio y leer varios `.md` con navegación clara sin depender de features opcionales.

## Fase 2: Búsqueda e indexación

### Objetivo

Permitir búsqueda rápida a nivel proyecto.

### Entregables

- índice SQLite FTS5,
- reindexado inicial,
- consulta por texto,
- búsqueda por path, heading y contenido.

### Tareas

1. Diseñar esquema SQLite:
   - tabla de documentos,
   - tabla de headings,
   - virtual table FTS5.
2. Implementar `search_index.py`.
3. Indexar:
   - path,
   - título,
   - headings,
   - contenido plano.
4. Añadir UI de búsqueda con resultados navegables.
5. Resolver apertura del documento seleccionado desde resultados.

### Criterio de cierre

La búsqueda devuelve resultados relevantes y abre el archivo correcto en el contexto adecuado.

## Fase 3: Hot reload

### Objetivo

Actualizar la interfaz cuando cambie el archivo activo o el índice del proyecto.

### Entregables

- watcher de archivos,
- refresco del documento abierto,
- reindexado incremental.

### Tareas

1. Implementar `file_watcher.py` con `watchdog`.
2. Detectar cambios sobre:
   - archivo abierto,
   - directorio indexado.
3. Refrescar preview sin reiniciar la app.
4. Invalidar y regenerar entradas del índice afectadas.

### Criterio de cierre

Editar un `.md` externo se refleja automáticamente en la TUI.

## Fase 4: Adaptadores enriquecidos

### Objetivo

Soportar contenido especial sin comprometer el núcleo.

### Entregables

- render opcional de Mermaid,
- charts en terminal,
- detección de capacidades del terminal,
- fallback para terminales sin soporte gráfico.

### Tareas

1. Implementar detección de bloques especiales desde el parser.
2. Crear `mermaid_cli.py` para ejecutar Mermaid CLI como dependencia opcional.
3. Crear `plotext_adapter.py` para charts terminal.
4. Implementar `capabilities.py` para detectar:
   - Kitty graphics,
   - soporte ANSI razonable,
   - presencia de `chafa`,
   - presencia de binarios externos.
5. Implementar política de degradación:
   - preferir render enriquecido,
   - caer a texto o placeholder útil,
   - nunca bloquear lectura del documento completo.

### Criterio de cierre

Los bloques especiales se renderizan cuando el entorno lo permite y fallan de forma controlada cuando no.

## Fase 5: Pulido y endurecimiento

### Objetivo

Llevar el proyecto de prototipo útil a herramienta robusta.

### Entregables

- caché selectiva,
- pruebas TUI y async,
- manejo de errores consistente,
- métricas básicas de rendimiento,
- documentación de uso.

### Tareas

1. Añadir caché para renders costosos.
2. Cubrir parsing, indexado y degradación con tests.
3. Añadir pruebas async para flujos `Textual`.
4. Endurecer errores de IO, paths inválidos y dependencias faltantes.
5. Completar documentación de usuario y desarrollo.

### Criterio de cierre

El proyecto es instalable, testeable y suficientemente estable para uso diario sobre repositorios reales.

## Diseño modular

## CLI

Responsable de:

- parsear argumentos,
- resolver modo de apertura,
- lanzar la app TUI con estado inicial.

No debe:

- parsear Markdown,
- indexar archivos,
- renderizar bloques complejos.

## Core

Responsable de:

- modelos de dominio,
- carga de proyecto,
- parsing estructural de Markdown,
- detección de capacidades del entorno.

Debe permanecer libre de detalles fuertes de UI.

## Services

Responsable de:

- indexación,
- watch de archivos,
- caché,
- coordinación de tareas de soporte.

## Renderers

Responsable de:

- transformar estructuras parseadas en salida visible,
- encapsular reglas de render para Markdown, código, Mermaid, charts e imágenes.

## Adapters

Responsable de:

- interactuar con binarios, protocolos y librerías opcionales,
- aislar dependencias externas del resto del código.

## UI

Responsable de:

- layout,
- widgets,
- interacción del usuario,
- sincronización entre selección, preview, TOC y búsqueda.

## Riesgos y mitigaciones

### Riesgo 1

`Textual` + render de Markdown puede volverse complejo si se mezcla parsing y UI.

Mitigación:

- mantener parsing y render como capas independientes,
- pasar modelos limpios a la UI.

### Riesgo 2

Mermaid e imágenes pueden introducir dependencias frágiles por plataforma.

Mitigación:

- tratarlas como extras opcionales,
- aislarlas en adaptadores,
- ofrecer fallback textual claro.

### Riesgo 3

La búsqueda puede degradarse en proyectos grandes.

Mitigación:

- usar SQLite FTS5 desde el principio,
- separar indexado inicial y reindexado incremental.

### Riesgo 4

El hot reload puede generar refrescos excesivos o estados inconsistentes.

Mitigación:

- debounce de eventos,
- invalidación localizada,
- actualizar solo el documento afectado cuando sea posible.

## Orden exacto recomendado

1. Bootstrap del proyecto y tooling.
2. CLI mínima con apertura de path.
3. Descubrimiento de archivos `.md`.
4. Parser estructural de Markdown.
5. Render básico y layout TUI.
6. TOC lateral y navegación.
7. Índice FTS5 y búsqueda.
8. Hot reload con `watchdog`.
9. Integraciones opcionales: charts, Mermaid, imágenes.
10. Pulido, pruebas y documentación final.

## Definición práctica de MVP 1

El MVP 1 está listo cuando:

- abre un archivo o directorio,
- lista documentos Markdown del proyecto,
- renderiza correctamente contenido común,
- muestra TOC navegable,
- permite buscar,
- reacciona a cambios del archivo abierto,
- no depende de binarios externos opcionales para ser útil.

## Próximo paso recomendado

Después de esta documentación, el siguiente paso lógico es implementar la Fase 0 completa:

1. crear `pyproject.toml`,
2. montar `src/mdscope`,
3. dejar `mdscope --help`,
4. levantar una app `Textual` mínima con layout de tres paneles.
