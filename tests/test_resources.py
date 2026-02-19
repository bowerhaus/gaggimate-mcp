"""Tests for MCP resource endpoints."""

import pytest
from pathlib import Path
from unittest.mock import patch

from mcp.server.fastmcp import FastMCP

from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.resources import (
    register_resources,
    _list_markdown_files,
    _read_markdown_file,
)


@pytest.fixture
def tmp_knowledge(tmp_path):
    """Create a temporary knowledge directory with sample files."""
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (knowledge_dir / "ESPRESSO_BASICS.md").write_text("# Espresso Basics\nContent here.")
    (knowledge_dir / "PRESSURE_GUIDE.md").write_text("# Pressure Guide\nMore content.")
    return knowledge_dir


@pytest.fixture
def tmp_coffees(tmp_path):
    """Create a temporary coffees directory with sample files."""
    coffees_dir = tmp_path / "coffees"
    coffees_dir.mkdir()
    (coffees_dir / "ethiopia-washed.md").write_text("# Ethiopia Washed\nGreat coffee.")
    return coffees_dir


@pytest.fixture
def tmp_user(tmp_path):
    """Create a temporary user directory with setup and grind map."""
    user_dir = tmp_path / "user"
    user_dir.mkdir()
    (user_dir / "user-setup.md").write_text("# User Setup\nMy equipment.")
    (user_dir / "grind-map.md").write_text("# Grind Map\nMy settings.")
    (user_dir / "user-setup.example.md").write_text("# Example Setup\nTemplate.")
    (user_dir / "grind-map.example.md").write_text("# Example Grind Map\nTemplate.")
    return user_dir


@pytest.fixture
def config_with_dirs(tmp_knowledge, tmp_coffees, tmp_user):
    """Create a config pointing to temp directories."""
    return GaggimateConfig(
        knowledge_dir=tmp_knowledge,
        coffees_dir=tmp_coffees,
        user_dir=tmp_user,
    )


@pytest.fixture
def mcp_with_resources(config_with_dirs):
    """Create a FastMCP instance with resources registered."""
    mcp = FastMCP("test-gaggimate")
    register_resources(mcp, config_with_dirs)
    return mcp


# ── Helper function tests ───────────────────────────────────────────


class TestListMarkdownFiles:
    """Tests for _list_markdown_files helper."""

    def test_lists_md_files(self, tmp_knowledge):
        """Should return all .md files sorted by name."""
        files = _list_markdown_files(tmp_knowledge)
        assert len(files) == 2
        assert files[0]["name"] == "ESPRESSO_BASICS"
        assert files[0]["filename"] == "ESPRESSO_BASICS.md"
        assert files[1]["name"] == "PRESSURE_GUIDE"

    def test_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        assert _list_markdown_files(empty_dir) == []

    def test_nonexistent_directory(self, tmp_path):
        """Should return empty list for nonexistent directory."""
        assert _list_markdown_files(tmp_path / "nope") == []

    def test_ignores_hidden_files(self, tmp_path):
        """Should skip files starting with a dot."""
        d = tmp_path / "mixed"
        d.mkdir()
        (d / "visible.md").write_text("yes")
        (d / ".hidden.md").write_text("no")
        files = _list_markdown_files(d)
        assert len(files) == 1
        assert files[0]["name"] == "visible"

    def test_ignores_non_md_files(self, tmp_path):
        """Should only list .md files."""
        d = tmp_path / "mixed"
        d.mkdir()
        (d / "doc.md").write_text("yes")
        (d / "data.json").write_text("{}")
        (d / ".gitkeep").write_text("")
        files = _list_markdown_files(d)
        assert len(files) == 1
        assert files[0]["filename"] == "doc.md"


class TestReadMarkdownFile:
    """Tests for _read_markdown_file helper."""

    def test_read_with_extension(self, tmp_knowledge):
        """Should read file when .md extension is included."""
        content = _read_markdown_file(tmp_knowledge, "ESPRESSO_BASICS.md")
        assert "# Espresso Basics" in content

    def test_read_without_extension(self, tmp_knowledge):
        """Should read file when .md extension is omitted."""
        content = _read_markdown_file(tmp_knowledge, "ESPRESSO_BASICS")
        assert "# Espresso Basics" in content

    def test_file_not_found(self, tmp_knowledge):
        """Should raise FileNotFoundError with helpful message."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            _read_markdown_file(tmp_knowledge, "NONEXISTENT")

    def test_file_not_found_lists_available(self, tmp_knowledge):
        """Should list available files in the error message."""
        with pytest.raises(FileNotFoundError, match="ESPRESSO_BASICS.md"):
            _read_markdown_file(tmp_knowledge, "NONEXISTENT")

    def test_path_traversal_dotdot(self, tmp_knowledge):
        """Should reject path traversal with '..'."""
        with pytest.raises(ValueError, match="Invalid file name"):
            _read_markdown_file(tmp_knowledge, "../etc/passwd")

    def test_path_traversal_slash(self, tmp_knowledge):
        """Should reject names with forward slashes."""
        with pytest.raises(ValueError, match="Invalid file name"):
            _read_markdown_file(tmp_knowledge, "sub/file")

    def test_path_traversal_backslash(self, tmp_knowledge):
        """Should reject names with backslashes."""
        with pytest.raises(ValueError, match="Invalid file name"):
            _read_markdown_file(tmp_knowledge, "sub\\file")


# ── Resource registration tests ──────────────────────────────────────


class TestResourceRegistration:
    """Tests for register_resources function."""

    @pytest.mark.asyncio
    async def test_resources_registered(self, mcp_with_resources):
        """Should register static resources."""
        resources = await mcp_with_resources.list_resources()
        uris = [str(r.uri) for r in resources]
        assert "gaggimate://knowledge" in uris
        assert "gaggimate://coffees" in uris
        assert "gaggimate://user/setup" in uris
        assert "gaggimate://user/grind-map" in uris

    @pytest.mark.asyncio
    async def test_resource_templates_registered(self, mcp_with_resources):
        """Should register resource templates."""
        templates = await mcp_with_resources.list_resource_templates()
        template_uris = [t.uriTemplate for t in templates]
        assert "gaggimate://knowledge/{filename}" in template_uris
        assert "gaggimate://coffees/{filename}" in template_uris


# ── Knowledge resource tests ─────────────────────────────────────────


class TestKnowledgeResources:
    """Tests for knowledge resource endpoints."""

    @pytest.mark.asyncio
    async def test_knowledge_index(self, mcp_with_resources):
        """Should list all knowledge files."""
        result = await mcp_with_resources.read_resource("gaggimate://knowledge")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "ESPRESSO_BASICS" in text
        assert "PRESSURE_GUIDE" in text

    @pytest.mark.asyncio
    async def test_knowledge_index_empty(self, tmp_path):
        """Should handle empty knowledge directory gracefully."""
        empty = tmp_path / "empty_knowledge"
        empty.mkdir()
        config = GaggimateConfig(
            knowledge_dir=empty,
            coffees_dir=tmp_path / "c",
            user_dir=tmp_path / "u",
        )
        mcp = FastMCP("test")
        register_resources(mcp, config)

        result = await mcp.read_resource("gaggimate://knowledge")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "No knowledge files found" in text

    @pytest.mark.asyncio
    async def test_read_knowledge_file(self, mcp_with_resources):
        """Should read a specific knowledge file."""
        result = await mcp_with_resources.read_resource(
            "gaggimate://knowledge/ESPRESSO_BASICS.md"
        )
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "# Espresso Basics" in text
        assert "Content here." in text


# ── Coffee resource tests ────────────────────────────────────────────


class TestCoffeeResources:
    """Tests for coffee resource endpoints."""

    @pytest.mark.asyncio
    async def test_coffees_index(self, mcp_with_resources):
        """Should list all coffee files."""
        result = await mcp_with_resources.read_resource("gaggimate://coffees")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "ethiopia-washed" in text

    @pytest.mark.asyncio
    async def test_coffees_index_empty(self, tmp_path):
        """Should handle empty coffees directory."""
        empty = tmp_path / "empty_coffees"
        empty.mkdir()
        config = GaggimateConfig(
            knowledge_dir=tmp_path / "k",
            coffees_dir=empty,
            user_dir=tmp_path / "u",
        )
        mcp = FastMCP("test")
        register_resources(mcp, config)

        result = await mcp.read_resource("gaggimate://coffees")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "No coffee files found" in text

    @pytest.mark.asyncio
    async def test_read_coffee_file(self, mcp_with_resources):
        """Should read a specific coffee file."""
        result = await mcp_with_resources.read_resource(
            "gaggimate://coffees/ethiopia-washed.md"
        )
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "# Ethiopia Washed" in text


# ── User resource tests ──────────────────────────────────────────────


class TestUserResources:
    """Tests for user resource endpoints."""

    @pytest.mark.asyncio
    async def test_read_user_setup(self, mcp_with_resources):
        """Should read user setup file."""
        result = await mcp_with_resources.read_resource("gaggimate://user/setup")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "# User Setup" in text
        assert "My equipment" in text

    @pytest.mark.asyncio
    async def test_user_setup_missing_shows_example(self, tmp_path):
        """Should show example template when user-setup.md is missing."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        (user_dir / "user-setup.example.md").write_text("# Example\nTemplate content.")

        config = GaggimateConfig(
            knowledge_dir=tmp_path / "k",
            coffees_dir=tmp_path / "c",
            user_dir=user_dir,
        )
        mcp = FastMCP("test")
        register_resources(mcp, config)

        result = await mcp.read_resource("gaggimate://user/setup")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "not configured" in text
        assert "Example Template" in text
        assert "Template content." in text

    @pytest.mark.asyncio
    async def test_user_setup_missing_no_example(self, tmp_path):
        """Should show basic message when both files are missing."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()

        config = GaggimateConfig(
            knowledge_dir=tmp_path / "k",
            coffees_dir=tmp_path / "c",
            user_dir=user_dir,
        )
        mcp = FastMCP("test")
        register_resources(mcp, config)

        result = await mcp.read_resource("gaggimate://user/setup")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "not configured" in text
        assert "manage_user_setup" in text

    @pytest.mark.asyncio
    async def test_read_grind_map(self, mcp_with_resources):
        """Should read grind map file."""
        result = await mcp_with_resources.read_resource("gaggimate://user/grind-map")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "# Grind Map" in text
        assert "My settings" in text

    @pytest.mark.asyncio
    async def test_grind_map_missing_shows_example(self, tmp_path):
        """Should show example template when grind-map.md is missing."""
        user_dir = tmp_path / "user"
        user_dir.mkdir()
        (user_dir / "grind-map.example.md").write_text("# Example Grind\nGrind template.")

        config = GaggimateConfig(
            knowledge_dir=tmp_path / "k",
            coffees_dir=tmp_path / "c",
            user_dir=user_dir,
        )
        mcp = FastMCP("test")
        register_resources(mcp, config)

        result = await mcp.read_resource("gaggimate://user/grind-map")
        text = result[0].content if hasattr(result[0], "content") else str(result[0])
        assert "not configured" in text
        assert "Grind template." in text
