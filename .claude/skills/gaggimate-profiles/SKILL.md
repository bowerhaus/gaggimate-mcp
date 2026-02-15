---
name: gaggimate-profiles
description: Create and upload custom Gaggimate extraction profiles. Use when user asks to create a profile, wants to adjust pressure/flow curves, mentions bloom, turbo, or flat profiles, or says "/gaggimate-profiles".
---

<command-name>gaggimate-profiles</command-name>

# Gaggimate Profile Creation Skill

Create, refine, and upload custom extraction profiles for Gaggimate-equipped machines.

## Reference Files (load on demand)

Read these when needed — don't load all at once:

| File | Load When |
|------|-----------|
| `desktop-app-skills/references/gaggimate-profiles/SCHEMA.md` | Need field definitions, pump modes, stop conditions |
| `desktop-app-skills/references/gaggimate-profiles/PHASE_TEMPLATES.md` | Building phase sequences |
| `desktop-app-skills/references/gaggimate-profiles/STYLE_GUIDE.md` | Choosing profile style for the coffee |
| `desktop-app-skills/references/gaggimate-profiles/BLOOM_PROFILES.md` | Creating bloom-style profiles |
| `desktop-app-skills/references/gaggimate-profiles/FLOW_PROFILES.md` | Flow-based profiles (turbo, flat) |
| `desktop-app-skills/references/gaggimate-profiles/BASKET_PROFILES.md` | Basket-specific adjustments |
| `desktop-app-skills/references/gaggimate-profiles/TROUBLESHOOTING.md` | Profile upload or device errors |

---

## Workflow

### 1. GATHER Info

Read before starting:
- `user-setup.md` — basket size, scale type, machine variant (Standard vs Pro)
- Active coffee's `coffees/{roaster}-{name}.md` — roast level, processing, current profiles

Ask if not clear from context:
- Target coffee (roast level and processing method)
- Desired shot style (classic / bloom / turbo / allonge)
- Pressure target (or let the knowledge guide it)

### 2. SELECT Profile Pattern

Use the Pressure x Roast x Processing matrix from `agent-knowledge/PRESSURE_GUIDE.md`:

| | Light | Medium | Dark |
|---|---|---|---|
| **Washed** | 8-9 bar | 9 bar | 7-8 bar |
| **Natural** | 7-8 bar | 8-9 bar | 6-7 bar |
| **Honey** | 7-9 bar | 8-9 bar | 7-8 bar |
| **Anaerobic/CM** | 6-8 bar | 7-8 bar | 6-7 bar |

**Profile style by roast:**
- Light washed: classic 9 bar or bloom-slide
- Light natural/anaerobic: bloom with pressure decline (controls fermentation intensity)
- Medium any: classic or flat
- Dark: lower pressure (7-8 bar), short pre-infusion

### 3. SELECT Temperature

| Roast | Temp |
|-------|------|
| Light | 94-96 degrees C |
| Medium | 92-94 degrees C |
| Medium-Dark | 90-92 degrees C |
| Dark | 88-90 degrees C |

### 4. BUILD Profile JSON

Read `desktop-app-skills/references/gaggimate-profiles/SCHEMA.md` for field definitions.

**Critical volumetric target check:** The profile's stop condition must match the user's dose x ratio.
- Example: 22g dose, 1:2.5 ratio = 55g target
- Library profiles in `agent-knowledge/PROFILE_LIBRARY.md` are sized for 22g — adjust for other basket sizes

Always add `[AI]` suffix to the profile label (e.g., `"Bloom Slide [AI]"`).

### 5. EXPLAIN Choices

Before uploading, explain:
- Why this pressure for this roast/process combination
- What the bloom phase does (if applicable)
- What the user should expect on the first shot

### 6. UPLOAD to Device

Ask for confirmation: "I've created a [style] profile for this [process] [origin] — shall I upload it to your machine?"

If confirmed:
```
manage_profile(action="create", profile_name="[Name] [AI]", temperature=X, phases=[...])
```

### 7. SAVE to Coffee File

**Repo first, device second.** The coffee file is the source of truth.

After successful upload, update the active coffee's `coffees/{roaster}-{name}.md`:
- Add a row to the Profiles table: Profile name, Style, Temp, Pressure, Ratio, Notes
- If storing the full JSON is useful, note it inline or as a code block

---

## Profile JSON Structure

```json
{
  "label": "Profile Name [AI]",
  "temperature": 94.0,
  "phases": [
    {
      "name": "Pre-infusion",
      "pump_mode": "flow",
      "pump_value": 2.0,
      "duration": 8,
      "transition": "instant"
    },
    {
      "name": "Main",
      "pump_mode": "pressure",
      "pump_value": 8.5,
      "stop_condition": "volume",
      "stop_value": 55.0
    }
  ]
}
```

See `desktop-app-skills/references/gaggimate-profiles/SCHEMA.md` for all fields and valid values.

---

## Quick Reference

**User asks for bloom profile on light natural:**
- Bloom (low flow, 8-10s) + pressure ramp to 7.5-8 bar + gentle decline
- Temp: 94-96 degrees C, Ratio: 1:2.5

**User asks for fast/turbo shot:**
- Coarse grind, 6-7 bar, 1:2.5-1:3 ratio, minimal pre-infusion
- See `desktop-app-skills/references/gaggimate-profiles/FLOW_PROFILES.md`

**User reports profile isn't uploading:**
- See `desktop-app-skills/references/gaggimate-profiles/TROUBLESHOOTING.md`
- Try `diagnose_connection()` first
