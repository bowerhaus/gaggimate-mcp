#!/usr/bin/env python3
"""
Knowledge Deduplication Analysis Tool
======================================

Measures the state of documentation across the gaggimate-mcp project to track
deduplication progress. Produces:

1. **Word count baseline** — total words per file, per directory, grand total
2. **Keyness analysis** — domain-specific terms overrepresented vs general English
3. **TF-IDF analysis** — terms that distinguish individual files from the corpus
4. **Concept duplication report** — domain concepts appearing in 3+ files
5. **Known duplication tracker** — specific patterns from the dedup plan

Run from project root:
    python scripts/analyze_knowledge.py

Output is written to stdout (human-readable) and optionally to
    scripts/analysis_report.json (machine-readable baseline snapshot).

No external dependencies — uses only Python stdlib.
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories we analyse — these are the documentation layers
SCAN_DIRS = {
    "knowledge": PROJECT_ROOT / "knowledge",
    "agent-instructions": PROJECT_ROOT / "agent-instructions",
    "agent-skills": PROJECT_ROOT / "agent-skills",
    "docs": PROJECT_ROOT / "docs",
    "README": PROJECT_ROOT,  # special: only README.md
}

# File extensions to include
INCLUDE_EXTENSIONS = {".md"}

# Files to always include even if outside SCAN_DIRS
EXTRA_FILES = [
    PROJECT_ROOT / "README.md",
]

# Minimum word length for analysis (skip 'a', 'of', etc.)
MIN_WORD_LENGTH = 3

# ---------------------------------------------------------------------------
# Common English words — top ~300 from various frequency lists
# Used as baseline for keyness calculation. These are words we expect
# to be common in ANY English text, not domain-specific.
# ---------------------------------------------------------------------------

COMMON_ENGLISH = {
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "her",
    "was", "one", "our", "out", "has", "his", "how", "its", "may", "new",
    "now", "old", "see", "way", "who", "did", "get", "got", "him", "let",
    "say", "she", "too", "use", "very", "when", "come", "each", "make",
    "like", "long", "look", "many", "some", "than", "them", "then", "what",
    "will", "with", "been", "call", "also", "back", "only", "even", "just",
    "from", "have", "more", "much", "over", "such", "take", "into", "year",
    "your", "could", "after", "about", "know", "most", "made", "find", "here",
    "thing", "other", "this", "that", "these", "those", "they", "their",
    "there", "where", "which", "while", "would", "should", "because",
    "through", "before", "between", "being", "under", "never", "still",
    "every", "first", "last", "work", "well", "same", "need", "good", "give",
    "does", "done", "going", "great", "help", "keep", "used", "using", "want",
    "time", "very", "when", "been", "have", "each", "high", "part", "real",
    "might", "must", "right", "small", "start", "different", "another",
    "example", "following", "however", "important", "including",
    "large", "often", "possible", "without", "number", "people",
    "place", "point", "provide", "second", "since", "three", "always",
    "both", "change", "end", "hand", "read", "line", "name", "data",
    "based", "case", "general", "group", "means", "level", "note", "will",
    "next", "above", "below", "full", "table", "value", "values", "set",
    "type", "form", "key", "best", "show", "file", "files", "section",
    "list", "add", "run", "per", "day", "see", "two", "top", "low",
    "try", "put", "left", "less", "move", "own", "sure", "turn", "around",
    "close", "open", "create", "default", "include", "main", "option",
    "options", "result", "results", "single", "specific", "standard",
    "support", "system", "text", "version", "current", "document",
    "information", "order", "process", "reference", "within", "available",
    "common", "content", "ensure", "instead", "manual", "output",
    "particular", "related", "require", "required", "similar",
    "update", "whether", "during", "already", "several",
    "called", "contain", "contains", "consider", "define", "defined",
    "description", "detail", "details", "directly", "either", "especially",
    "expect", "expected", "field", "further", "given", "guide",
    "known", "likely", "method", "model", "original", "primary",
    "rather", "simply", "source", "step", "steps", "suggest",
    "true", "false", "null", "none", "http", "https", "www", "com",
    "also", "just", "will", "can", "more", "some", "than", "when",
    "what", "with", "from", "have", "this", "that", "they", "their",
}

# Known domain concepts to specifically track across files
# (from the deduplication plan)
# Patterns must be specific enough to avoid false positives.
TRACKED_CONCEPTS = {
    "scott rao": "Scott Rao channeling rule",
    "sour.{1,20}bitter.{1,40}channeling": "Sour+bitter→channeling rule",
    "variable hierarchy": "Variable hierarchy (grind→ratio→temp)",
    "grind.*ratio.*temp(?:erature)?": "Variable hierarchy (grind→ratio→temp)",
    "diagnostic.tree": "Diagnostic decision trees",
    "decision.tree": "Diagnostic decision trees",
    "weight.estimation|never.ask.*weight": "Weight estimation rule",
    "pump.mode": "Pump modes reference",
    "shot.style": "Shot style parameters",
    "turbo.shot": "Turbo shot style",
    "bloom.shot": "Bloom shot style",
    "allonge|allongé": "Allongé shot style",
    "pre-?infusion": "Pre-infusion technique",
    "puck.prep": "Puck preparation",
    "94.*96.*°?c|light.roast.*temp": "Light roast temperature (94-96°C)",
    "stop.condition": "Profile stop conditions",
}

# Layers that are agent-facing (loaded by the LLM at runtime).
# We track duplication WITHIN these layers most carefully.
AGENT_FACING_LAYERS = {"knowledge", "agent-instructions", "agent-skills"}

# Layers that are internal docs / planning — duplication here matters less.
INTERNAL_LAYERS = {"docs", "README", "other"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_relative(path: Path) -> str:
    """Return path relative to project root."""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def tokenize(text: str) -> list[str]:
    """Simple word tokenizer: lowercase, alpha-only tokens, min length."""
    return [
        w
        for w in re.findall(r"[a-zA-ZÀ-ÿ]+(?:[-'][a-zA-ZÀ-ÿ]+)*", text.lower())
        if len(w) >= MIN_WORD_LENGTH
    ]


def collect_files() -> list[Path]:
    """Collect all markdown files to analyse."""
    files: set[Path] = set()

    for label, directory in SCAN_DIRS.items():
        if label == "README":
            # Only grab README.md from root
            readme = directory / "README.md"
            if readme.exists():
                files.add(readme)
            continue

        if not directory.exists():
            continue

        for root, _dirs, filenames in os.walk(directory):
            for fn in filenames:
                fp = Path(root) / fn
                if fp.suffix.lower() in INCLUDE_EXTENSIONS:
                    files.add(fp)

    for fp in EXTRA_FILES:
        if fp.exists():
            files.add(fp)

    return sorted(files)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class FileStats:
    path: str
    layer: str
    word_count: int
    line_count: int
    tokens: Counter = field(default_factory=Counter)


@dataclass
class AnalysisResult:
    timestamp: str
    files: list[FileStats]
    layer_totals: dict[str, dict]
    grand_total_words: int
    grand_total_lines: int
    keyness_top: list[tuple[str, float, int]]
    tfidf_per_file: dict[str, list[tuple[str, float]]]
    concept_locations: dict[str, list[str]]
    tracked_concept_locations: dict[str, list[str]]


# ---------------------------------------------------------------------------
# Layer classification
# ---------------------------------------------------------------------------


def classify_layer(path: Path) -> str:
    """Classify a file into its documentation layer."""
    rel = get_relative(path)
    if rel == "README.md":
        return "README"
    if rel.startswith("knowledge/"):
        return "knowledge"
    if rel.startswith("agent-instructions/"):
        return "agent-instructions"
    if rel.startswith("agent-skills/"):
        return "agent-skills"
    if rel.startswith("docs/"):
        return "docs"
    return "other"


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------


def compute_file_stats(files: list[Path]) -> list[FileStats]:
    """Read each file, compute word/line counts and token frequencies."""
    stats = []
    for fp in files:
        text = fp.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        tokens = tokenize(text)
        counter = Counter(tokens)
        stats.append(
            FileStats(
                path=get_relative(fp),
                layer=classify_layer(fp),
                word_count=len(tokens),
                line_count=len(lines),
                tokens=counter,
            )
        )
    return stats


def compute_keyness(
    all_stats: list[FileStats], top_n: int = 80
) -> list[tuple[str, float, int]]:
    """
    Keyness analysis: find terms overrepresented in our corpus vs general English.

    For each term, keyness = repo_frequency_rank_boost / common_english_penalty.
    Terms NOT in common English get a high keyness score.
    Terms IN common English get suppressed.

    Returns list of (term, keyness_score, raw_count) sorted by keyness descending.
    """
    # Aggregate all tokens across the corpus
    corpus_counts: Counter = Counter()
    for fs in all_stats:
        corpus_counts.update(fs.tokens)

    total_tokens = sum(corpus_counts.values())
    if total_tokens == 0:
        return []

    keyness_scores = []
    for term, count in corpus_counts.items():
        if count < 3:  # skip very rare terms
            continue

        repo_freq = count / total_tokens

        # Terms in common English get suppressed
        if term in COMMON_ENGLISH:
            # Still include but with low score (they're expected)
            keyness = repo_freq * 0.01
        else:
            # Domain terms get boosted — the rarer in English, the higher the score
            # We use a simple heuristic: repo frequency as-is (since it's not in common English)
            keyness = repo_freq * 100  # scale up for readability

        keyness_scores.append((term, keyness, count))

    keyness_scores.sort(key=lambda x: x[1], reverse=True)
    return keyness_scores[:top_n]


def compute_tfidf(
    all_stats: list[FileStats], top_n_per_file: int = 10
) -> dict[str, list[tuple[str, float]]]:
    """
    TF-IDF: find terms that distinguish individual files from the corpus.

    TF = term_count_in_doc / total_tokens_in_doc
    IDF = log(N / df) where df = number of docs containing the term
    """
    n_docs = len(all_stats)
    if n_docs == 0:
        return {}

    # Document frequency: how many docs contain each term
    doc_freq: Counter = Counter()
    for fs in all_stats:
        for term in fs.tokens:
            doc_freq[term] += 1

    result = {}
    for fs in all_stats:
        if fs.word_count == 0:
            continue

        tfidf_scores = []
        for term, count in fs.tokens.items():
            if term in COMMON_ENGLISH:
                continue
            if count < 2:
                continue

            tf = count / fs.word_count
            idf = math.log(n_docs / doc_freq[term]) if doc_freq[term] > 0 else 0
            tfidf = tf * idf

            if tfidf > 0:
                tfidf_scores.append((term, round(tfidf, 5)))

        tfidf_scores.sort(key=lambda x: x[1], reverse=True)
        result[fs.path] = tfidf_scores[:top_n_per_file]

    return result


def find_concept_duplication(
    all_stats: list[FileStats], min_files: int = 3, top_n: int = 60
) -> dict[str, list[str]]:
    """
    Find domain-specific terms (high keyness) that appear in 3+ files.
    This is the automatic concept duplication detector.
    """
    # First get domain terms (not in common English, count >= 3)
    corpus_counts: Counter = Counter()
    for fs in all_stats:
        corpus_counts.update(fs.tokens)

    domain_terms = {
        term
        for term, count in corpus_counts.items()
        if count >= 5 and term not in COMMON_ENGLISH and len(term) >= 4
    }

    # For each domain term, find which files contain it
    term_files: dict[str, list[str]] = defaultdict(list)
    for fs in all_stats:
        for term in domain_terms:
            if fs.tokens.get(term, 0) >= 2:  # at least 2 occurrences in the file
                term_files[term].append(fs.path)

    # Filter to terms in min_files+ files, sort by file count descending
    duplicated = {
        term: sorted(files)
        for term, files in term_files.items()
        if len(files) >= min_files
    }

    # Sort by number of files (most spread out first)
    sorted_items = sorted(duplicated.items(), key=lambda x: len(x[1]), reverse=True)
    return dict(sorted_items[:top_n])


def find_tracked_concepts(
    files: list[Path], agent_facing_only: bool = False
) -> dict[str, list[str]]:
    """
    Search for specifically tracked concept patterns from the dedup plan.
    Uses regex matching on the raw file text.

    If agent_facing_only=True, only report files in AGENT_FACING_LAYERS.
    """
    results: dict[str, list[str]] = defaultdict(list)

    for fp in files:
        layer = classify_layer(fp)
        if agent_facing_only and layer not in AGENT_FACING_LAYERS:
            continue

        text = fp.read_text(encoding="utf-8", errors="replace").lower()
        rel = get_relative(fp)

        for pattern, label in TRACKED_CONCEPTS.items():
            if re.search(pattern, text):
                if rel not in results[label]:
                    results[label].append(rel)

    # Sort by number of files descending
    return dict(
        sorted(results.items(), key=lambda x: len(x[1]), reverse=True)
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 78
THIN_SEP = "-" * 78


def print_header(title: str) -> None:
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def report_word_counts(all_stats: list[FileStats]) -> dict[str, dict]:
    """Print and return word count report."""
    print_header("WORD COUNT BASELINE")

    # Group by layer
    layers: dict[str, list[FileStats]] = defaultdict(list)
    for fs in all_stats:
        layers[fs.layer].append(fs)

    layer_totals = {}

    # Define display order
    layer_order = ["knowledge", "agent-instructions", "agent-skills", "docs", "README", "other"]

    for layer in layer_order:
        if layer not in layers:
            continue
        files = sorted(layers[layer], key=lambda x: x.path)

        total_words = sum(f.word_count for f in files)
        total_lines = sum(f.line_count for f in files)
        layer_totals[layer] = {
            "files": len(files),
            "words": total_words,
            "lines": total_lines,
        }

        print(f"\n  [{layer}] — {len(files)} files, {total_words:,} words, {total_lines:,} lines")
        print(f"  {THIN_SEP}")

        for fs in files:
            print(f"    {fs.word_count:>6,} words  {fs.line_count:>5,} lines  {fs.path}")

    grand_words = sum(t["words"] for t in layer_totals.values())
    grand_lines = sum(t["lines"] for t in layer_totals.values())
    grand_files = sum(t["files"] for t in layer_totals.values())

    # Agent-facing subtotal (the layers the LLM actually loads)
    af_words = sum(t["words"] for l, t in layer_totals.items() if l in AGENT_FACING_LAYERS)
    af_lines = sum(t["lines"] for l, t in layer_totals.items() if l in AGENT_FACING_LAYERS)
    af_files = sum(t["files"] for l, t in layer_totals.items() if l in AGENT_FACING_LAYERS)

    print(f"\n  {'=' * 58}")
    print(f"  AGENT-FACING TOTAL: {af_files} files, {af_words:,} words, {af_lines:,} lines")
    print(f"  ALL DOCS TOTAL:     {grand_files} files, {grand_words:,} words, {grand_lines:,} lines")
    print(f"  {'=' * 58}")

    return layer_totals


def report_keyness(keyness: list[tuple[str, float, int]]) -> None:
    """Print keyness analysis."""
    print_header("KEYNESS ANALYSIS — Domain-Specific Terms")
    print("  Terms overrepresented in our docs vs general English.")
    print("  Higher score = more domain-specific.\n")

    print(f"  {'Rank':<6} {'Term':<30} {'Score':>8} {'Count':>7}")
    print(f"  {THIN_SEP}")

    for i, (term, score, count) in enumerate(keyness, 1):
        print(f"  {i:<6} {term:<30} {score:>8.3f} {count:>7}")


def report_tfidf(tfidf: dict[str, list[tuple[str, float]]]) -> None:
    """Print TF-IDF report — only for files with interesting terms."""
    print_header("TF-IDF ANALYSIS — Distinctive Terms Per File")
    print("  Terms that distinguish each file from the rest of the corpus.\n")

    for filepath, terms in sorted(tfidf.items()):
        if not terms:
            continue
        # Only show files with at least one term scoring > 0.001
        if terms[0][1] < 0.001:
            continue

        print(f"  {filepath}")
        for term, score in terms[:7]:
            bar = "█" * int(score * 500)
            print(f"    {term:<25} {score:.4f}  {bar}")
        print()


def report_concept_duplication(concepts: dict[str, list[str]]) -> None:
    """Print automatic concept duplication report."""
    print_header("CONCEPT DUPLICATION — Auto-Detected (3+ files)")
    print("  Domain terms appearing with ≥2 occurrences in ≥3 files.\n")

    if not concepts:
        print("  No significant concept duplication detected.")
        return

    print(f"  {'Term':<25} {'Files':>5}  Locations")
    print(f"  {THIN_SEP}")

    for term, files in concepts.items():
        loc_str = ", ".join(files[:4])
        if len(files) > 4:
            loc_str += f", +{len(files)-4} more"
        print(f"  {term:<25} {len(files):>5}  {loc_str}")


def report_tracked_concepts(tracked: dict[str, list[str]]) -> None:
    """Print tracked concept locations from the dedup plan."""
    print_header("TRACKED CONCEPT LOCATIONS — From Dedup Plan")
    print("  Specific patterns we're monitoring for deduplication.\n")

    for label, files in tracked.items():
        severity = "HIGH" if len(files) >= 4 else "MED" if len(files) >= 3 else "low"
        marker = "!!!" if severity == "HIGH" else " ! " if severity == "MED" else "   "
        print(f"  {marker} {label} — found in {len(files)} files:")
        for f in files:
            print(f"        {f}")
        print()


def report_summary(
    layer_totals: dict[str, dict],
    concepts: dict[str, list[str]],
    tracked_agent: dict[str, list[str]],
    tracked_all: dict[str, list[str]],
) -> None:
    """Print executive summary."""
    print_header("EXECUTIVE SUMMARY")

    grand_words = sum(t["words"] for t in layer_totals.values())
    grand_files = sum(t["files"] for t in layer_totals.values())
    af_words = sum(t["words"] for l, t in layer_totals.items() if l in AGENT_FACING_LAYERS)
    af_files = sum(t["files"] for l, t in layer_totals.items() if l in AGENT_FACING_LAYERS)

    print(f"\n  All documentation:    {grand_files} files, {grand_words:,} words")
    print(f"  Agent-facing layers:  {af_files} files, {af_words:,} words")
    print()

    print("  Layer breakdown:")
    for layer, totals in sorted(layer_totals.items(), key=lambda x: x[1]["words"], reverse=True):
        pct = (totals["words"] / grand_words * 100) if grand_words else 0
        af_tag = " [AGENT]" if layer in AGENT_FACING_LAYERS else ""
        bar = "█" * int(pct / 2)
        print(f"    {layer:<25} {totals['words']:>6,} words ({pct:>5.1f}%)  {bar}{af_tag}")

    # Duplication metrics — agent-facing only
    high_dup = sum(1 for files in tracked_agent.values() if len(files) >= 4)
    med_dup = sum(1 for files in tracked_agent.values() if 3 <= len(files) < 4)
    auto_concepts = len(concepts)

    print(f"\n  Tracked concept duplication (agent-facing layers only):")
    print(f"    HIGH (4+ files): {high_dup} concepts")
    print(f"    MED  (3 files):  {med_dup} concepts")
    print(f"    Total tracked:   {len(tracked_agent)} concept patterns")
    print(f"\n  Tracked concept duplication (all layers):")
    print(f"    Total tracked:   {len(tracked_all)} concept patterns")
    print(f"\n  Auto-detected duplication:")
    print(f"    Domain terms in 3+ files: {auto_concepts}")

    print(f"\n  Timestamp: {datetime.now().isoformat()}")
    print(f"  Save this baseline to track deduplication progress.\n")


# ---------------------------------------------------------------------------
# JSON snapshot
# ---------------------------------------------------------------------------


def save_snapshot(
    all_stats: list[FileStats],
    layer_totals: dict[str, dict],
    keyness: list[tuple[str, float, int]],
    tfidf: dict[str, list[tuple[str, float]]],
    concepts: dict[str, list[str]],
    tracked_all: dict[str, list[str]],
    tracked_agent: dict[str, list[str]],
    output_path: Path,
) -> None:
    """Save machine-readable snapshot for before/after comparison."""
    af_totals = {l: t for l, t in layer_totals.items() if l in AGENT_FACING_LAYERS}
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "grand_total": {
            "files": sum(t["files"] for t in layer_totals.values()),
            "words": sum(t["words"] for t in layer_totals.values()),
            "lines": sum(t["lines"] for t in layer_totals.values()),
        },
        "agent_facing_total": {
            "files": sum(t["files"] for t in af_totals.values()),
            "words": sum(t["words"] for t in af_totals.values()),
            "lines": sum(t["lines"] for t in af_totals.values()),
        },
        "layer_totals": layer_totals,
        "files": [
            {
                "path": fs.path,
                "layer": fs.layer,
                "words": fs.word_count,
                "lines": fs.line_count,
            }
            for fs in all_stats
        ],
        "keyness_top_30": [
            {"term": t, "score": round(s, 4), "count": c}
            for t, s, c in keyness[:30]
        ],
        "concept_duplication": {
            term: {"file_count": len(files), "files": files}
            for term, files in concepts.items()
        },
        "tracked_concepts_all": {
            label: {"file_count": len(files), "files": files}
            for label, files in tracked_all.items()
        },
        "tracked_concepts_agent_facing": {
            label: {"file_count": len(files), "files": files}
            for label, files in tracked_agent.items()
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"  Snapshot saved to: {get_relative(output_path)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"\n{'#' * 78}")
    print(f"  GAGGIMATE-MCP KNOWLEDGE ANALYSIS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#' * 78}")

    # Collect and analyse files
    files = collect_files()
    if not files:
        print("ERROR: No markdown files found. Are you running from the project root?")
        sys.exit(1)

    print(f"\n  Scanning {len(files)} markdown files...")

    all_stats = compute_file_stats(files)

    # 1. Word counts
    layer_totals = report_word_counts(all_stats)
    grand_words = sum(t["words"] for t in layer_totals.values())
    grand_lines = sum(t["lines"] for t in layer_totals.values())

    # 2. Keyness
    keyness = compute_keyness(all_stats, top_n=80)
    report_keyness(keyness)

    # 3. TF-IDF
    tfidf = compute_tfidf(all_stats, top_n_per_file=10)
    report_tfidf(tfidf)

    # 4. Auto concept duplication
    concepts = find_concept_duplication(all_stats, min_files=3, top_n=60)
    report_concept_duplication(concepts)

    # 5. Tracked concepts — agent-facing layers only (what matters for dedup)
    tracked_agent = find_tracked_concepts(files, agent_facing_only=True)
    print_header("TRACKED CONCEPTS — Agent-Facing Layers Only")
    print("  These are the duplications that matter most for dedup.")
    print("  (knowledge + agent-instructions + agent-skills)\n")
    report_tracked_concepts(tracked_agent)

    # 5b. Tracked concepts — all files (for reference)
    tracked_all = find_tracked_concepts(files, agent_facing_only=False)
    print_header("TRACKED CONCEPTS — All Files (reference)")
    report_tracked_concepts(tracked_all)

    # 6. Executive summary
    report_summary(layer_totals, concepts, tracked_agent, tracked_all)

    # 7. Save JSON snapshot
    snapshot_path = PROJECT_ROOT / "scripts" / "analysis_report.json"
    save_snapshot(all_stats, layer_totals, keyness, tfidf, concepts, tracked_all, tracked_agent, snapshot_path)

    print(f"\n{'#' * 78}")
    print(f"  DONE — Use this report as baseline before deduplication.")
    print(f"  Re-run after changes to measure impact.")
    print(f"{'#' * 78}\n")


if __name__ == "__main__":
    main()
