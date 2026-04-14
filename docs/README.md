# MDScope Docs

## Visión

MDScope será una aplicación TUI para navegar y leer documentación técnica escrita en Markdown directamente desde terminal. La meta es ofrecer una experiencia cercana a un lector moderno de conocimiento técnico, pero optimizada para entorno CLI: explorador de archivos, preview renderizado, tabla de contenidos, búsqueda rápida y soporte progresivo para contenido enriquecido.

## Objetivo del producto

Resolver un problema concreto: leer y consultar documentación de proyectos sin salir del terminal, sin perder estructura ni legibilidad, y sin depender de una GUI.

Casos de uso principales:

- Abrir un archivo Markdown concreto.
- Abrir un directorio de documentación y navegar entre archivos.
- Buscar por contenido, títulos y secciones.
- Seguir la estructura del documento mediante un TOC lateral.
- Ver bloques de código con resaltado.
- Añadir soporte opcional para Mermaid, charts e imágenes según capacidades del terminal.

## Stack recomendado

Núcleo:

- Lenguaje: Python 3.12+
- Gestión del proyecto: `uv`
- CLI: `Typer`
- TUI: `Textual`
- Render terminal: `Rich`
- Parser Markdown: `markdown-it-py`
- Búsqueda local: SQLite con FTS5

Capas opcionales:

- Hot reload: `watchdog`
- Charts en terminal: `plotext` + `textual-plotext`
- Diagramas Mermaid: `@mermaid-js/mermaid-cli`
- Imágenes inline: protocolo gráfico de Kitty
- Fallback visual: `chafa`

Calidad:

- Testing: `pytest` + `pytest-asyncio`
- Lint y format: `Ruff`
- Tipado estático: `mypy`

## Decisión técnica principal

La base no debe ser una colección de librerías aisladas. El proyecto debe construirse sobre una TUI fuerte, con adaptadores opcionales para capacidades extra.

Esto implica:

- `Textual` como shell principal de interacción.
- `Rich` y `markdown-it-py` como capa de render e interpretación.
- Adaptadores desacoplados para Mermaid, charts e imágenes.
- Detección de capacidades del terminal para degradación elegante.

## MVP recomendado

El MVP 1 debe enfocarse en entregar valor usable rápido, evitando inflar el alcance.

Incluye:

- `Typer`
- `Textual`
- `Rich`
- `markdown-it-py`
- SQLite FTS5
- `watchdog`
- `pytest`
- `Ruff`

Funciones del MVP:

- Abrir archivo o directorio.
- Explorar archivos Markdown del proyecto.
- Renderizar Markdown legible en terminal.
- Mostrar TOC del documento actual.
- Buscar dentro del proyecto.
- Refrescar la vista cuando cambie el archivo abierto.

Queda fuera del MVP:

- Mermaid renderizado inline.
- Charts enriquecidos.
- Imágenes inline por protocolo gráfico.
- Caché avanzada de render.
- Atajos complejos o personalización extensa de layout.

## Roadmap

### Fase 0

Bootstrap del proyecto:

- Inicializar proyecto con `uv`.
- Definir `pyproject.toml`.
- Crear estructura de paquetes.
- Configurar lint, tests y tipado.

### Fase 1

Núcleo del lector:

- Implementar CLI base `mdscope`.
- Construir layout TUI principal.
- Cargar archivos Markdown y renderizarlos.
- Extraer headings para TOC lateral.
- Navegar entre archivos del proyecto.

### Fase 2

Búsqueda y refresco:

- Indexar proyecto con SQLite FTS5.
- Resolver búsqueda por archivo, heading y contenido.
- Integrar `watchdog` para hot reload.

### Fase 3

Capas opcionales:

- Soporte Mermaid por adaptador externo.
- Soporte charts con `plotext`.
- Detección de terminal compatible con Kitty graphics.
- Fallback con `chafa`.

### Fase 4

Pulido:

- Mejoras de UX y keybindings.
- Persistencia ligera de estado.
- Caché de previews.
- Suite de pruebas para flujos TUI.

## Arquitectura objetivo

```text
mdscope/
├── pyproject.toml
├── README.md
├── docs/
│   ├── README.md
│   └── implementation-plan.md
├── src/mdscope/
│   ├── cli/
│   │   └── app.py
│   ├── core/
│   │   ├── models.py
│   │   ├── project_loader.py
│   │   ├── markdown_parser.py
│   │   └── capabilities.py
│   ├── services/
│   │   ├── search_index.py
│   │   ├── file_watcher.py
│   │   └── cache.py
│   ├── renderers/
│   │   ├── markdown_renderer.py
│   │   ├── code_renderer.py
│   │   ├── mermaid_renderer.py
│   │   ├── chart_renderer.py
│   │   └── image_renderer.py
│   ├── ui/
│   │   ├── app.py
│   │   ├── screens/
│   │   ├── widgets/
│   │   └── styles/
│   └── adapters/
│       ├── mermaid_cli.py
│       ├── plotext_adapter.py
│       ├── kitty_adapter.py
│       └── chafa_adapter.py
└── tests/
```

## Principios de implementación

- Mantener el núcleo operativo sin depender de Mermaid, charts ni imágenes.
- Tratar cada integración externa como adaptador opcional.
- Separar parsing, render, servicios e interfaz para evitar acoplamiento.
- Diseñar desde el inicio con modelos tipados y pruebas del dominio.
- Preferir degradación elegante sobre fallos duros cuando el entorno no soporte una capacidad.

## Siguiente documento

El detalle de ejecución está en [`implementation-plan.md`](implementation-plan.md).

El checklist consolidado de trabajo por etapas está en [`phases.md`](phases.md).

La continuación del roadmap, ya sobre el producto base funcionando, está en [`post-mvp-phases.md`](post-mvp-phases.md).
