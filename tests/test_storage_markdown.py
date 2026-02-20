"""Tests for markdown storage helpers."""

import pytest
from pathlib import Path

from gaggimate_mcp.storage.markdown import (
    MarkdownStorage,
    _sanitize_filename,
    build_coffee_markdown,
    append_journal_entry,
    build_grind_map_markdown,
    append_grind_entry,
    build_brewing_insights_markdown,
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

    def test_path_traversal_dotdot_rejected(self, storage):
        with pytest.raises(ValueError, match="Invalid filename"):
            storage.read("../etc/passwd")

    def test_path_traversal_absolute_rejected(self, storage):
        with pytest.raises(ValueError, match="Invalid filename"):
            storage.read("/etc/passwd")

    def test_path_traversal_backslash_rejected(self, storage):
        with pytest.raises(ValueError, match="Invalid filename"):
            storage.write("foo\\bar", "content")

    def test_path_traversal_exists_returns_false(self, storage):
        """exists() should return False for traversal attempts, not raise."""
        assert storage.exists("../etc/passwd") is False

    def test_path_traversal_write_rejected(self, storage):
        with pytest.raises(ValueError, match="Invalid filename"):
            storage.write("../../evil", "content")

    def test_path_traversal_delete_rejected(self, storage):
        with pytest.raises(ValueError, match="Invalid filename"):
            storage.delete("../secret")


# ── Coffee markdown builder ──────────────────────────────────────────


class TestBuildCoffeeMarkdown:
    """Tests for build_coffee_markdown."""

    def test_minimal_coffee(self):
        md = build_coffee_markdown(coffee_name="Azul", roaster="Jack LeFleur")
        assert "# Jack LeFleur — Azul" in md
        assert "| **Roaster** | Jack LeFleur |" in md
        assert "| **Coffee name** | Azul |" in md
        assert "## Brewing Journal" in md
        assert "## Key Insights" in md

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
            approach="Start with Lever Decline profile at 92C, 15g dose targeting 1:2.5 ratio. Medium roast suggests 8-9 bar peak pressure.",
        )
        assert "| **Origin** | Brazil |" in md
        assert "| **Process** | Pulped Natural |" in md
        assert "| **Roast date** | 02 Feb 2026 |" in md
        assert "## Approach" in md
        assert "Lever Decline profile at 92C" in md
        assert "## Brewing Journal" in md
        assert "## Key Insights" in md

    def test_optional_fields_omitted(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="Roaster")
        assert "Origin" not in md
        assert "Approach" not in md

    def test_approach_section(self):
        md = build_coffee_markdown(
            coffee_name="Test",
            roaster="Roaster",
            approach="Try a flat 6 bar profile for this light roast washed Ethiopian.",
        )
        assert "## Approach" in md
        assert "flat 6 bar profile" in md


# ── Shot log appending ────────────────────────────────────────────────


class TestAppendJournalEntry:
    """Tests for append_journal_entry."""

    def test_append_to_empty_journal(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="R")
        updated = append_journal_entry(
            md,
            date="2026-02-19",
            headline="Grind 10, Lever Decline — 4/5",
            body="Good body and sweetness. Slightly fast — try grind 11 next time.",
        )
        assert "### 2026-02-19 — Grind 10, Lever Decline — 4/5" in updated
        assert "Good body and sweetness" in updated
        # Placeholder text should be removed
        assert "No entries yet" not in updated

    def test_append_multiple_entries(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="R")
        md = append_journal_entry(md, date="Day 1", headline="First shot")
        md = append_journal_entry(md, date="Day 2", headline="Second shot")
        assert "Day 1" in md
        assert "Day 2" in md
        # Day 2 should come after Day 1
        assert md.index("Day 1") < md.index("Day 2")

    def test_append_without_journal_section(self):
        """Should add a Brewing Journal section if missing."""
        md = "# Test Coffee\n\nSome content."
        updated = append_journal_entry(
            md, date="2026-02-19", headline="Test entry", body="Analysis here."
        )
        assert "## Brewing Journal" in updated
        assert "2026-02-19" in updated
        assert "Analysis here." in updated

    def test_default_date(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="R")
        updated = append_journal_entry(md, headline="Quick note")
        # Should have today's date (just check there's a ### heading with current year)
        lines = [l for l in updated.split("\n") if l.startswith("### 20")]
        assert len(lines) == 1

    def test_entry_without_headline(self):
        md = build_coffee_markdown(coffee_name="Test", roaster="R")
        updated = append_journal_entry(md, date="2026-03-01", body="Just a note.")
        assert "### 2026-03-01" in updated
        assert "Just a note." in updated


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

    def test_pipe_in_value_escaped(self):
        """Pipes in field values should be escaped to prevent table corruption."""
        md = build_grind_map_markdown()
        updated = append_grind_entry(md, coffee="Coffee | Special", grind="10|11")
        # The raw pipe should be escaped
        assert "Coffee \\| Special" in updated
        assert "10\\|11" in updated

    def test_newline_in_value_stripped(self):
        """Newlines in field values should be stripped to prevent table corruption."""
        md = build_grind_map_markdown()
        updated = append_grind_entry(md, coffee="Coffee\nWith\nNewlines", grind="10")
        assert "\n" not in updated.split("Coffee")[1].split("|")[0]


# ── Brewing insights ──────────────────────────────────────────────────


class TestBuildBrewingInsightsMarkdown:
    """Tests for build_brewing_insights_markdown."""

    def test_template_has_title(self):
        md = build_brewing_insights_markdown()
        assert "# Brewing Insights" in md

    def test_template_has_sections(self):
        md = build_brewing_insights_markdown()
        assert "## By Origin & Process" in md
        assert "## By Profile Style" in md
        assert "## General Patterns" in md

    def test_template_has_placeholder_text(self):
        md = build_brewing_insights_markdown()
        assert "No entries yet" in md
