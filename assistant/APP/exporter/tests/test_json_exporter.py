"""
Tests for JSON Exporter (Phase B)

These tests enforce:
- File creation
- Schema preservation
- Metadata presence
- Output boundary rules
"""

import json
from pathlib import Path
import pytest

from assistant.APP.exporter.json_exporter import export_json


@pytest.fixture
def sample_summary():
    return {
        "summary": {
            "title": "Sample Title",
            "key_points": ["Point A", "Point B"],
            "details": []
        },
        "confidence": {
            "level": "high",
            "rationale": "Clear input"
        },
        "metadata": {
            "source_id": "test-source-001",
            "generated_by": "assistant/APP",
            "schema_version": "1.0.0"
        }
    }


def test_export_json_creates_file(tmp_path, sample_summary):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    output_path = export_json(sample_summary, str(output_dir))

    assert Path(output_path).exists(), "JSON export file was not created"


def test_export_json_preserves_schema(tmp_path, sample_summary):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    output_path = export_json(sample_summary, str(output_dir))

    with open(output_path, "r", encoding="utf-8") as f:
        exported = json.load(f)

    assert exported == sample_summary, "Exporter modified summarizer output"


def test_export_json_contains_metadata(tmp_path, sample_summary):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    output_path = export_json(sample_summary, str(output_dir))

    with open(output_path, "r", encoding="utf-8") as f:
        exported = json.load(f)

    assert "metadata" in exported
    assert exported["metadata"]["generated_by"] == "assistant/APP"