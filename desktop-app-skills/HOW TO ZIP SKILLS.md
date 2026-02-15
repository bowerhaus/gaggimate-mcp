# How to Zip Skills for Claude Desktop

Skills are distributed as ZIP files. Each ZIP contains `SKILL.md` at the root, plus a `references/` folder if the skill has on-demand reference files.

## Claude Desktop ZIP Rule

**`SKILL.md` must be at the root of the ZIP — not inside a subfolder.**

Claude Desktop reads the skill by looking for `SKILL.md` at the top level of the archive. If it's nested (e.g., `gaggimate-profiles/SKILL.md`), the skill will not be recognized.

```
✅ Correct ZIP structure:
SKILL.md              ← at root
references/
  EXAMPLES.md
  ...

❌ Wrong ZIP structure:
gaggimate-profiles/
  SKILL.md            ← nested — Claude Desktop won't find it
  references/
    EXAMPLES.md
```

This means you must `cd` into a staging directory before running `zip`, not zip the folder itself.

## Commands

Run from the `desktop-app-skills/` folder:

```bash
# gaggimate-profiles
cd /tmp && rm -rf skill-zip && mkdir -p skill-zip/references
cp /path/to/gaggimate-mcp/desktop-app-skills/gaggimate-profiles.md skill-zip/SKILL.md
cp /path/to/gaggimate-mcp/desktop-app-skills/references/gaggimate-profiles/*.md skill-zip/references/
cd skill-zip && zip -r /path/to/gaggimate-mcp/desktop-app-skills/gaggimate-profiles-skill.zip SKILL.md references/

# new-coffee
cd /tmp && rm -rf skill-zip && mkdir -p skill-zip/references
cp /path/to/gaggimate-mcp/desktop-app-skills/new-coffee.md skill-zip/SKILL.md
cp /path/to/gaggimate-mcp/desktop-app-skills/references/new-coffee/*.md skill-zip/references/
cd skill-zip && zip -r /path/to/gaggimate-mcp/desktop-app-skills/new-coffee-skill.zip SKILL.md references/

# diagnose
cd /tmp && rm -rf skill-zip && mkdir -p skill-zip/references
cp /path/to/gaggimate-mcp/desktop-app-skills/diagnose.md skill-zip/SKILL.md
cp /path/to/gaggimate-mcp/desktop-app-skills/references/diagnose/*.md skill-zip/references/
cd skill-zip && zip -r /path/to/gaggimate-mcp/desktop-app-skills/diagnose-skill.zip SKILL.md references/

# feedback (no references)
cd /tmp && rm -rf skill-zip && mkdir skill-zip
cp /path/to/gaggimate-mcp/desktop-app-skills/feedback.md skill-zip/SKILL.md
cd skill-zip && zip -r /path/to/gaggimate-mcp/desktop-app-skills/feedback-skill.zip SKILL.md

# consult (no references)
cd /tmp && rm -rf skill-zip && mkdir skill-zip
cp /path/to/gaggimate-mcp/desktop-app-skills/consult.md skill-zip/SKILL.md
cd skill-zip && zip -r /path/to/gaggimate-mcp/desktop-app-skills/consult-skill.zip SKILL.md
```

## Installing in Claude Desktop

1. Open Claude Desktop → **Settings → Capabilities → Skills → Add**
2. Upload the relevant `.zip` file(s)
3. The skill will be available in all conversations

## Files in this folder

| File | Description |
|------|-------------|
| `gaggimate-profiles.md` | Profile creation with conditional reference loading |
| `new-coffee.md` | Research new beans, recommend parameters, upload profile |
| `diagnose.md` | Shot telemetry analysis with taste correlation |
| `feedback.md` | Shot feedback loop: gather → analyze → record → recommend |
| `consult.md` | Knowledge Q&A router (cites correct knowledge file) |
| `references/` | Reference files loaded on-demand by skills that support it |
| `*-skill.zip` | Packaged skills ready for Claude Desktop upload |
