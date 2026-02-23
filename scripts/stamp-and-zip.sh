#!/usr/bin/env bash
# stamp-and-zip.sh — Stamp version into instructions + skills, then zip skills.
# Run this before uploading to Claude Desktop.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Get commit info
HASH=$(git rev-parse --short HEAD)
DATE=$(date +%Y-%m-%d)
VERSION="${HASH} (${DATE})"

echo "Stamping version: ${VERSION}"
echo ""

# --- Stamp INSTRUCTIONS.md ---
INSTRUCTIONS="agent-instructions/INSTRUCTIONS.md"
# Match the version line pattern and replace it
sed -i '' "s/^> \*\*Version:\*\* .*/> **Version:** \`${HASH}\` \| Last updated: ${DATE}/" "$INSTRUCTIONS"
echo "  Updated ${INSTRUCTIONS}"

# --- Stamp all skill files ---
SKILLS=(diagnose feedback gaggimate-profiles knowledge-lookup new-coffee)
for skill in "${SKILLS[@]}"; do
    SKILL_FILE="agent-skills/${skill}/SKILL.md"
    # Replace the version line inside metadata: block in YAML frontmatter
    sed -i '' "s|^  version: .*|  version: ${VERSION}|" "$SKILL_FILE"
    echo "  Updated ${SKILL_FILE}"
done

# --- Zip all skills ---
echo ""
echo "Zipping skills..."
cd agent-skills
for skill in "${SKILLS[@]}"; do
    zip -r "../${skill}-skill.zip" "${skill}/" -q
    echo "  Created ${skill}-skill.zip"
done
cd "$REPO_ROOT"

# --- Summary ---
echo ""
echo "============================================"
echo "  Ready to upload to Claude Desktop"
echo "  Version: ${HASH} | ${DATE}"
echo "============================================"
echo ""
echo "1. Copy instructions from:"
echo "   ${INSTRUCTIONS}"
echo ""
echo "2. Upload these skill zips:"
for skill in "${SKILLS[@]}"; do
    echo "   ${skill}-skill.zip"
done
echo ""
echo "Tip: open the zips folder in Finder:"
echo "   open ."
