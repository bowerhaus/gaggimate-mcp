"""Markdown file storage helpers for user data.

Provides read/write operations for markdown files managed by MCP tools:
- User setup (user/user-setup.md)
- Coffee tracking files (coffees/*.md)
- Grind map (user/grind-map.md)
"""

from pathlib import Path
from datetime import datetime

from gaggimate_mcp.logging_config import get_logger

logger = get_logger(__name__)


def _sanitize_filename(name: str) -> str:
    """Convert a display name to a safe filename.

    Args:
        name: Human-readable name (e.g. "Jack LeFleur — Azul")

    Returns:
        Safe filename without extension (e.g. "jacklefleur-azul")
    """
    # Lowercase and replace common separators
    safe = name.lower()
    # Replace em-dash, en-dash, and other separators with hyphen
    for char in ["—", "–", ":", "|"]:
        safe = safe.replace(char, "-")
    # Replace spaces and underscores with hyphens
    safe = safe.replace(" ", "-").replace("_", "-")
    # Keep only alphanumeric and hyphens
    safe = "".join(c for c in safe if c.isalnum() or c == "-")
    # Collapse multiple hyphens and strip leading/trailing
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-")


class MarkdownStorage:
    """Read/write markdown files in a directory."""

    def __init__(self, directory: Path):
        """Initialize storage for a directory.

        Args:
            directory: Path to the directory
        """
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def read(self, filename: str) -> str | None:
        """Read a markdown file.

        Args:
            filename: Filename with or without .md extension

        Returns:
            File contents, or None if file doesn't exist
        """
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        path = self.directory / filename
        if not path.is_file():
            return None

        return path.read_text(encoding="utf-8")

    def write(self, filename: str, content: str) -> Path:
        """Write content to a markdown file (create or overwrite).

        Args:
            filename: Filename with or without .md extension
            content: Full markdown content to write

        Returns:
            Path to the written file
        """
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        path = self.directory / filename
        path.write_text(content, encoding="utf-8")
        return path

    def exists(self, filename: str) -> bool:
        """Check if a markdown file exists.

        Args:
            filename: Filename with or without .md extension

        Returns:
            True if file exists
        """
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        return (self.directory / filename).is_file()

    def delete(self, filename: str) -> bool:
        """Delete a markdown file.

        Args:
            filename: Filename with or without .md extension

        Returns:
            True if file was deleted, False if it didn't exist
        """
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        path = self.directory / filename
        if path.is_file():
            path.unlink()
            return True
        return False

    def list_files(self) -> list[str]:
        """List all markdown files in the directory.

        Returns:
            List of filenames (without .md extension)
        """
        if not self.directory.is_dir():
            return []

        return sorted(
            p.stem for p in self.directory.glob("*.md")
            if not p.name.startswith(".")
        )


def build_coffee_markdown(
    *,
    coffee_name: str,
    roaster: str,
    origin: str = "",
    process: str = "",
    variety: str = "",
    roast_level: str = "",
    roast_date: str = "",
    bag_size: str = "",
    roaster_notes: str = "",
    freshness_note: str = "",
    extraction_dose: str = "",
    extraction_yield: str = "",
    extraction_temp: str = "",
    extraction_grind: str = "",
    extraction_profile: str = "",
    extraction_notes: str = "",
    pressure_logic: str = "",
    additional_notes: str = "",
) -> str:
    """Build a coffee tracking markdown file.

    Args:
        coffee_name: Full coffee name
        roaster: Roaster name
        origin: Country/region of origin
        process: Processing method
        variety: Coffee variety
        roast_level: Roast level
        roast_date: Roast date string
        bag_size: Bag size
        roaster_notes: Tasting notes from roaster
        freshness_note: Freshness/peak window note
        extraction_dose: Recommended dose
        extraction_yield: Target yield
        extraction_temp: Temperature
        extraction_grind: Grind setting
        extraction_profile: Profile name
        extraction_notes: Additional extraction notes
        pressure_logic: Reasoning for pressure/profile choice
        additional_notes: Any additional notes

    Returns:
        Complete markdown string
    """
    lines = [f"# {roaster} — {coffee_name}", ""]

    # Bean Profile table
    lines.append("## Bean Profile")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| **Roaster** | {roaster} |")
    lines.append(f"| **Coffee name** | {coffee_name} |")
    if origin:
        lines.append(f"| **Origin** | {origin} |")
    if variety:
        lines.append(f"| **Variety** | {variety} |")
    if process:
        lines.append(f"| **Process** | {process} |")
    if roast_level:
        lines.append(f"| **Roast level** | {roast_level} |")
    if roast_date:
        lines.append(f"| **Roast date** | {roast_date} |")
    if bag_size:
        lines.append(f"| **Bag size** | {bag_size} |")
    if roaster_notes:
        lines.append(f"| **Roaster notes** | {roaster_notes} |")

    if freshness_note:
        lines.append("")
        lines.append(f"**Freshness note:** {freshness_note}")

    # Extraction Parameters
    if any([extraction_dose, extraction_yield, extraction_temp,
            extraction_grind, extraction_profile]):
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Extraction Parameters")
        lines.append("")
        lines.append("| Parameter | Value | Notes |")
        lines.append("|-----------|-------|-------|")
        if extraction_dose:
            lines.append(f"| **Dose** | {extraction_dose} | |")
        if extraction_yield:
            lines.append(f"| **Yield** | {extraction_yield} | |")
        if extraction_temp:
            lines.append(f"| **Temperature** | {extraction_temp} | |")
        if extraction_grind:
            lines.append(f"| **Grind** | {extraction_grind} | |")
        if extraction_profile:
            lines.append(f"| **Profile** | {extraction_profile} | |")

        if pressure_logic:
            lines.append("")
            lines.append(f"**Pressure logic:** {pressure_logic}")

        if extraction_notes:
            lines.append("")
            lines.append(f"**Notes:** {extraction_notes}")

    # Shot Log (empty starter)
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Shot Log")
    lines.append("")
    lines.append("| Date | Grind | Profile | Dose | Yield | Time | Rating | Notes |")
    lines.append("|------|-------|---------|------|-------|------|--------|-------|")

    if additional_notes:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Notes")
        lines.append("")
        lines.append(additional_notes)

    lines.append("")
    return "\n".join(lines)


def append_shot_to_coffee(
    content: str,
    *,
    date: str = "",
    grind: str = "",
    profile: str = "",
    dose: str = "",
    yield_g: str = "",
    time: str = "",
    rating: str = "",
    notes: str = "",
) -> str:
    """Append a shot log row to an existing coffee markdown file.

    Finds the Shot Log table and appends a new row.

    Args:
        content: Existing file content
        date: Shot date
        grind: Grind setting
        profile: Profile used
        dose: Dose in grams
        yield_g: Yield in grams
        time: Shot time
        rating: Rating (e.g. "4/5")
        notes: Shot notes

    Returns:
        Updated file content
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    row = f"| {date} | {grind} | {profile} | {dose} | {yield_g} | {time} | {rating} | {notes} |"

    # Find the shot log table header and append after the separator line
    lines = content.split("\n")
    insert_idx = None
    in_shot_log = False

    for i, line in enumerate(lines):
        if "## Shot Log" in line:
            in_shot_log = True
        elif in_shot_log and line.startswith("|---"):
            insert_idx = i + 1
            # Find the last row of the table (skip existing rows)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("|"):
                    insert_idx = j + 1
                else:
                    break
            break

    if insert_idx is not None:
        lines.insert(insert_idx, row)
    else:
        # No shot log section found — append one
        lines.append("")
        lines.append("## Shot Log")
        lines.append("")
        lines.append("| Date | Grind | Profile | Dose | Yield | Time | Rating | Notes |")
        lines.append("|------|-------|---------|------|-------|------|--------|-------|")
        lines.append(row)

    return "\n".join(lines)


def build_grind_map_markdown() -> str:
    """Build the initial grind map markdown file.

    Returns:
        Empty grind map template
    """
    return """# Grind Map

A personal record of successful grind settings that grows from your shots.

## Successful Settings

| Coffee | Roast | Process | Origin | Days Off Roast | Grind | Profile | Ratio | Temp | Rating | Date |
|--------|-------|---------|--------|----------------|-------|---------|-------|------|--------|------|

*Days Off Roast is optional — use "—" when roast date is unknown.*
*Grind notation: use your grinder's format.*

---

*This file is automatically updated when you rate shots 4–5 stars with grind settings provided.*
"""


def append_grind_entry(
    content: str,
    *,
    coffee: str = "",
    roast: str = "",
    process: str = "",
    origin: str = "",
    days_off_roast: str = "—",
    grind: str = "",
    profile: str = "",
    ratio: str = "",
    temp: str = "",
    rating: str = "",
    date: str = "",
) -> str:
    """Append a row to the grind map's Successful Settings table.

    Args:
        content: Existing grind map content
        coffee: Coffee name
        roast: Roast level
        process: Processing method
        origin: Origin country
        days_off_roast: Days since roast
        grind: Grind setting
        profile: Profile used
        ratio: Brew ratio
        temp: Temperature
        rating: Rating
        date: Date of shot

    Returns:
        Updated grind map content
    """
    if not date:
        date = datetime.now().strftime("%b %d")

    row = (
        f"| {coffee} | {roast} | {process} | {origin} | {days_off_roast} "
        f"| {grind} | {profile} | {ratio} | {temp} | {rating} | {date} |"
    )

    lines = content.split("\n")
    insert_idx = None

    for i, line in enumerate(lines):
        if line.startswith("|---") and "Grind" in lines[i - 1] if i > 0 else False:
            insert_idx = i + 1
            # Skip existing rows
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("|"):
                    insert_idx = j + 1
                else:
                    break
            break

    if insert_idx is not None:
        lines.insert(insert_idx, row)
    else:
        # Fallback: append table at end
        lines.append("")
        lines.append("## Successful Settings")
        lines.append("")
        lines.append(
            "| Coffee | Roast | Process | Origin | Days Off Roast "
            "| Grind | Profile | Ratio | Temp | Rating | Date |"
        )
        lines.append(
            "|--------|-------|---------|--------|----------------"
            "|-------|---------|-------|------|--------|------|"
        )
        lines.append(row)

    return "\n".join(lines)
