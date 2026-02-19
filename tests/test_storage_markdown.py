"""Tests for markdown storage helpers."""

import pytest
from pathlib import Path

from gaggimate_mcp.storage.markdown import (
    MarkdownStorage,
    _sanitize_filename,
    build_coffee_markdown,
    append_shot_to_coffee,
    build_grind_map_markdown,
    append_grind_entry,
)


# ── Filename sanitization ────────────────────────────────────────────


class TestSanitizeFilename:
    """Tests for _sanitize_filename helper."""

    def test_simple_name(self):
        assert _sanitize_filename("Ethiopia") == "ethiopia"

    def test_spaces_to_hyphens(self):
        assert _sanitize_filename("Jack LeFleur Azul") == "jack-lefleur-azul"

    def test_em_dash(self):
        assert _sanitize_filename("Jack LeFleur — Azul") == "jack-lefleur-azul"

    def test_special_chars_removed(self):
        assert _sanitize_filename("Hello! World?") == "hello-world"

    def test_multiple_hyphens_collapsed(self):
        assert _sanitize_filename("A --- B") == "a-b"

    def test_leading_trailing_stripped(self):
        assert _sanitize_filename("  — Hello — ") == "hello"

    def test_underscores_to_hyphens(self):
        assert _sanitize_filename("my_coffee_name") == "my-coffee-name"


# ── MarkdownStorage ──────────────────────────────────────────────────


class TestMarkdownStorage:
    """Tests for MarkdownStorage class."""

    @pytest.fixture
    def storage(self, tmp_path):
        return MarkdownStorage(tmp_path / "test_storage")

    def test_creates_directory(self, tmp_path):
        d = tmp_path / "new_dir"
        assert not d.exists()
        MarkdownStorage(d)
        assert d.exists()

    def test_write_and_read(self, storage):
        storage.write("test", "# Hello\nContent")
        result = storage.read("test")
        assert result == "# Hello\nContent"

    def test_write_with_extension(self, storage):
        storage.write("test.md", "content")
        assert storage.read("test") == "content"

    def test_read_nonexistent(self, storage):
        assert storage.read("missing") is None

    def test_exists(self, storage):
        assert not storage.exists("test")
        storage.write("test", "content")
        assert storage.exists("test")

    def test_exists_with_extension(self, storage):
        storage.write("test", "content")
        assert storage.exists("test.md")

    def test_delete(self, storage):
        storage.write("test", "content")
        assert storage.delete("test") is True
        assert storage.read("test") is None

    def test_delete_nonexistent(self, storage):
        assert storage.delete("missing") is False

    def test_list_files(self, storage):
        storage.write("alpha", "a")
        storage.write("beta", "b")
        storage.write("charlie", "c")
        files = storage.list_files()
        assert files == ["alpha", "beta", "charlie"]

    def test_list_files_empty(self, storage):
        assert storage.list_files() == []

    def test_overwrite(self, storage):
        storage.write("test", "v1")
        storage.write("test", "v2")
        assert storage.read("test") == "v2"


# ── Coffee markdown builder ──────────────────────────────────────────


class TestBuildCoffeeMarkdown:
    """Tests for build_coffee_markdown."""

    def test_minimal_coffee(self):
        md = build_coffee_markdown(coffee_name="Azul", roaster="Jack LeFleur")
        assert "# Jack LeFleur — Azul" in md
        assert "| **Roaster** | Jack LeFleur |" in md
        assert "| **Coffee name** | Azul |" in md
        assert "## Shot Log" in md

    def test_full_coffee(self):
        md = build_coffee_markdown(
            coffee_name="Azul",
            roaster="Jack LeFleur",
            origin="Brazil",
            process="Pulped Natural",
            variety="Yellow Catuai",
            roast_level="Medium",
            roast_date="02 Feb 2026",
            bag_size="250g",
            roaster_notes="Nuts, chocolate",
            freshness_note="Peak: 2 weeks after roast",
            extraction_dose="15g",
            extraction_yield="37g",
            extraction_temp="92°C",
            extraction_grind="10",
            extraction_profile="Lever Decline [AI]",
            pressure_logic="Medium roast → 8-9 bar",
        )
        assert "| **Origin** | Brazil |" in md
        assert "| **Process** | Pulped Natural |" in md
        assert "| **Roast date** | 02 Feb 2026 |" in md
        assert "## Extraction Parameters" in md
        assert "| **Dose** | 15g |" in md
        assert "**Pressure logic:** Medium roast" in md

    def test_optional_fields_omitted(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="Roaster")
        assert "Origin" not in md
        assert "Extraction Parameters" not in md

    def test_additional_notes(self):
        md = build_coffee_markdown(
            coffee_name="Test",
            roaster="Roaster",
            additional_notes="Some extra notes here",
        )
        assert "## Notes" in md
        assert "Some extra notes here" in md


# ── Shot log appending ────────────────────────────────────────────────


class TestAppendShotToCoffee:
    """Tests for append_shot_to_coffee."""

    def test_append_to_empty_shot_log(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="R")
        updated = append_shot_to_coffee(
            md,
            date="2026-02-19",
            grind="10",
            profile="Classic",
            dose="15g",
            yield_g="30g",
            time="28s",
            rating="4/5",
            notes="Good body",
        )
        assert "| 2026-02-19 | 10 | Classic | 15g | 30g | 28s | 4/5 | Good body |" in updated

    def test_append_multiple_shots(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="R")
        md = append_shot_to_coffee(md, date="Day 1", grind="10")
        md = append_shot_to_coffee(md, date="Day 2", grind="11")
        assert "Day 1" in md
        assert "Day 2" in md
        # Day 2 should come after Day 1
        assert md.index("Day 1") < md.index("Day 2")

    def test_append_without_shot_log_section(self):
        """Should add a shot log section if missing."""
        md = "# Test Coffee\n\nSome content."
        updated = append_shot_to_coffee(md, date="2026-02-19", grind="10")
        assert "## Shot Log" in updated
        assert "2026-02-19" in updated

    def test_default_date(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="R")
        updated = append_shot_to_coffee(md, grind="10")
        # Should have today's date (just check it's not empty)
        lines = [l for l in updated.split("\n") if l.startswith("| 20")]
        assert len(lines) == 1


# ── Grind map ─────────────────────────────────────────────────────────


class TestGrindMap:
    """Tests for grind map helpers."""

    def test_build_initial_grind_map(self):
        md = build_grind_map_markdown()
        assert "# Grind Map" in md
        assert "## Successful Settings" in md
        assert "| Coffee |" in md

    def test_append_grind_entry(self):
        md = build_grind_map_markdown()
        updated = append_grind_entry(
            md,
            coffee="Ethiopia Washed",
            roast="Light",
            process="Washed",
            origin="Ethiopia",
            grind="13D",
            profile="Classic 9 Bar",
            ratio="1:2",
            temp="93°C",
            rating="4",
            date="Feb 19",
        )
        assert "Ethiopia Washed" in updated
        assert "| Light |" in updated
        assert "13D" in updated

    def test_append_multiple_entries(self):
        md = build_grind_map_markdown()
        md = append_grind_entry(md, coffee="Coffee A", grind="10")
        md = append_grind_entry(md, coffee="Coffee B", grind="12")
        assert "Coffee A" in md
        assert "Coffee B" in md

    def test_default_days_off_roast(self):
        md = build_grind_map_markdown()
        updated = append_grind_entry(md, coffee="Test")
        assert "—" in updated
