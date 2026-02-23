#!/usr/bin/env bash
# stamp-and-zip.sh — Stamp version into instructions + skills, then zip skills.
# Run this before uploading to Claude Desktop.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

DATE=$(date +%Y-%m-%d)

# Helper: get the short hash of the last commit that changed a file (ignoring the version line itself)
last_content_hash() {
    local file="$1"
    # Get the last commit that changed the file
    git log -1 --format=%h -- "$file"
}

echo "Stamping per-file versions..."
echo ""

# --- Stamp INSTRUCTIONS.md ---
INSTRUCTIONS="agent-instructions/INSTRUCTIONS.md"
INST_HASH=$(last_content_hash "$INSTRUCTIONS")
sed -i '' "s/^> \*\*Version:\*\* .*/> **Version:** \`${INST_HASH}\` \| Last updated: ${DATE}/" "$INSTRUCTIONS"
echo "  ${INSTRUCTIONS} → ${INST_HASH} (${DATE})"

# --- Stamp all skill files ---
SKILLS=(diagnose feedback gaggimate-profiles knowledge-lookup new-coffee)
for skill in "${SKILLS[@]}"; do
    SKILL_FILE="agent-skills/${skill}/SKILL.md"
    SKILL_HASH=$(last_content_hash "$SKILL_FILE")
    SKILL_VERSION="${SKILL_HASH} (${DATE})"
    sed -i '' "s|^  version: .*|  version: ${SKILL_VERSION}|" "$SKILL_FILE"
    echo "  ${SKILL_FILE} → ${SKILL_HASH} (${DATE})"
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
