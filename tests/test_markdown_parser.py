from __future__ import annotations

from pathlib import Path

from mdscope.core.markdown_parser import parse_markdown_document, parse_markdown_text


def test_parse_markdown_extracts_headings_and_anchors(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    parsed = parse_markdown_text(
        source_path=source,
        raw_text="# Intro\n\n## Arquitectura Base\n\nTexto.\n",
    )

    assert [heading.text for heading in parsed.headings] == [
        "Intro",
        "Arquitectura Base",
    ]
    assert [heading.anchor for heading in parsed.headings] == [
        "intro",
        "arquitectura-base",
    ]
    assert parsed.headings[0].start_line == 0
    assert parsed.headings[0].end_line == 2
    assert parsed.headings[1].start_line == 2


def test_parse_markdown_detects_fence_blocks(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    parsed = parse_markdown_text(
        source_path=source,
        raw_text="```python\nprint('hola')\n```\n",
    )

    fence_blocks = [block for block in parsed.blocks if block.kind == "fence"]

    assert len(fence_blocks) == 1
    assert fence_blocks[0].info == "python"
    assert "print('hola')" in fence_blocks[0].text


def test_parse_markdown_classifies_special_fences(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    parsed = parse_markdown_text(
        source_path=source,
        raw_text="```mermaid\ngraph TD\nA-->B\n```\n\n```chart\nx: 1\n```\n",
    )

    assert [block.kind for block in parsed.blocks if block.kind in {"mermaid", "chart"}] == [
        "mermaid",
        "chart",
    ]


def test_parse_markdown_detects_image_blocks(tmp_path: Path) -> None:
    source = tmp_path / "guide.md"
    parsed = parse_markdown_text(
        source_path=source,
        raw_text="![Diagrama](./images/flow.png)\n",
    )

    image_blocks = [block for block in parsed.blocks if block.kind == "image"]

    assert len(image_blocks) == 1
    assert image_blocks[0].text == "./images/flow.png"
    assert image_blocks[0].meta == "Diagrama"


def test_parse_markdown_document_returns_error_document_for_missing_file(tmp_path: Path) -> None:
    parsed = parse_markdown_document(tmp_path / "missing.md")

    assert parsed.blocks[0].kind == "error"
    assert "Error de lectura" in parsed.raw_text


def test_extract_section_text_returns_heading_slice(tmp_path: Path) -> None:
    from mdscope.core.markdown_parser import extract_section_text

    source = tmp_path / "guide.md"
    parsed = parse_markdown_text(
        source_path=source,
        raw_text="# Intro\n\ntexto intro\n\n## Uso\n\ntexto uso\n",
    )

    section = extract_section_text(parsed, "uso")

    assert section == "## Uso\n\ntexto uso"
