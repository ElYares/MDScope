# Fases post-MVP de MDScope

Este documento define la siguiente etapa del proyecto ahora que el plan base ya esta funcional. La idea es no mezclar estas lineas de evolucion con el roadmap inicial: aqui ya no estamos construyendo el lector, sino volviendolo mas potente, instalable y agradable de usar.

## Orden recomendado

1. Fase 12: instalacion global y distribucion local
2. Fase 13: render real de Mermaid
3. Fase 14: charts terminal reales
4. Fase 15: empaquetado y release
5. Fase 16: mejoras de UX visual

## Fase 12: Instalacion global y distribucion local

### Objetivo

Poder usar MDScope desde cualquier carpeta sin depender de `uv run --directory ...`.

### Alcance

- exponer comandos globales `mdscope` y `MDScope`,
- documentar instalacion con `uv tool install`,
- documentar reinstalacion y desinstalacion,
- dejar claro el flujo recomendado para abrir proyectos y archivos externos.

### Entregables

- entrypoints globales definidos en `pyproject.toml`,
- documentacion de instalacion global,
- flujo de uso diario documentado,
- criterio de validacion manual desde otra carpeta.

### Tareas

1. Definir ambos scripts:
   - `mdscope`
   - `MDScope`
2. Documentar instalacion desde el repo local:
   - `uv tool install --from /ruta/al/repo MDScope`
3. Documentar reinstalacion tras cambios:
   - `uv tool install --reinstall --from /ruta/al/repo MDScope`
4. Documentar desinstalacion:
   - `uv tool uninstall mdscope`
5. Validar el flujo desde una carpeta ajena al repositorio.

### Flujo esperado para el usuario

Instalacion inicial:

```bash
uv tool install --from /home/elyarestark/develop/MDScope MDScope
```

Uso desde cualquier carpeta:

```bash
MDScope .
MDScope README.md
mdscope .
mdscope /ruta/a/docs
```

Actualizar instalacion global tras cambios:

```bash
uv tool install --reinstall --from /home/elyarestark/develop/MDScope MDScope
```

### Criterio de cierre

- el comando funciona desde una carpeta externa al repo,
- `MDScope .` abre la TUI sobre el directorio actual,
- `MDScope archivo.md` abre la TUI con ese archivo como documento activo.

## Fase 13: Render real de Mermaid

### Objetivo

Renderizar diagramas Mermaid reales cuando el entorno tenga el adaptador disponible.

### Alcance

- detectar bloques `mermaid`,
- invocar Mermaid CLI como adaptador externo,
- cachear render por bloque,
- degradar a placeholder cuando Mermaid CLI no este instalado.

### Entregables

- `adapters/mermaid_cli.py`,
- `renderers/mermaid_renderer.py`,
- deteccion de disponibilidad de Mermaid CLI,
- fallback limpio cuando falte el binario.

### Tareas

1. Definir un adaptador para `mmdc`.
2. Resolver carpeta temporal o cache de salidas.
3. Renderizar a `svg` o `png` segun estrategia elegida.
4. Integrar con el renderer de imagenes o fallback textual.
5. Añadir pruebas de deteccion y degradacion.

### Criterio de cierre

- un bloque Mermaid no solo se detecta: se renderiza cuando el adaptador existe,
- si el adaptador no existe, la app sigue siendo usable y explicita el fallback.

## Fase 14: Charts terminal reales

### Objetivo

Mostrar charts utiles dentro de la TUI sin depender de imagenes.

### Alcance

- soportar fences `chart`,
- convertir datos a graficas terminal con `plotext`,
- integrar el render como widget o bloque enriquecido.

### Entregables

- `adapters/plotext_adapter.py`,
- `renderers/chart_renderer.py`,
- fallback textual si el bloque no se puede interpretar.

### Tareas

1. Definir formato inicial soportado para `chart`.
2. Parsear contenido del bloque.
3. Renderizar con `plotext` o `textual-plotext`.
4. Ajustar al ancho del terminal.
5. Añadir validaciones y errores legibles.

### Criterio de cierre

- un bloque `chart` simple se ve como grafica real en terminal,
- si el contenido es invalido, el usuario ve un mensaje util en lugar de un fallo opaco.

## Fase 15: Empaquetado y release

### Objetivo

Dejar MDScope listo para distribucion mas estable fuera del entorno de desarrollo.

### Alcance

- versionado mas claro,
- build reproducible,
- instrucciones de publicacion,
- checklist de release.

### Entregables

- versionado de lanzamiento en `pyproject.toml`,
- comandos de build documentados,
- checklist de release en docs,
- validacion de instalacion desde wheel o source dist.

### Tareas

1. Definir politica de versionado.
2. Documentar `uv build`.
3. Probar instalacion desde artefactos generados.
4. Añadir notas de compatibilidad de terminal.
5. Dejar una guia de release minima.

### Criterio de cierre

- el proyecto se puede construir como paquete instalable,
- la instalacion desde artefacto produce el mismo comando funcional.

## Fase 16: Mejoras de UX visual

### Objetivo

Refinar la experiencia de lectura y navegacion para que la app se sienta menos prototipo y mas producto.

### Alcance

- mejor jerarquia visual,
- estados vacios mas claros,
- foco mas evidente,
- paneles mas equilibrados,
- pequeños detalles de ergonomia.

### Entregables

- estilos Textual refinados,
- mejor feedback en paneles de TOC y busqueda,
- estados de error y carga mas claros,
- keybindings visibles y consistentes.

### Tareas

1. Revisar layout y anchos por defecto.
2. Mejorar contraste de foco y seleccion.
3. Hacer mas claro el cambio entre TOC y resultados de busqueda.
4. Añadir ayuda contextual minima en UI.
5. Revisar legibilidad en terminales pequenos.

### Criterio de cierre

- la app comunica mejor lo que esta pasando,
- navegar entre archivos, TOC y resultados se siente natural sin leer el codigo ni la documentacion.
