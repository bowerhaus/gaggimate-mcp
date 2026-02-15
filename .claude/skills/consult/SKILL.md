---
name: consult
description: Answer espresso knowledge questions from authoritative knowledge files. Use when user asks about temperature, pressure, ratios, grind, freshness, milk steaming, baskets, extraction science, decaf, blends, or says "/consult". Routes to the right knowledge file rather than answering from training data.
---

<command-name>consult</command-name>

# Espresso Knowledge Consultation Skill

Route espresso questions to the right knowledge file and answer from authoritative sources — not from training data alone.

## Knowledge File Routing Table

| Question Type | Load File |
|---------------|-----------|
| Grind, ratio, temp basics, shot time, 5g rule, diagnostic decision tree | `agent-knowledge/ESPRESSO_BREWING_BASICS.md` |
| Sour vs bitter, tasting methodology, flavor wheel, extraction balance | `agent-knowledge/ESPRESSO_TASTING_GUIDE.md` |
| Pressure by roast/process, shot styles, turbo/ristretto parameters | `agent-knowledge/PRESSURE_GUIDE.md` |
| Channeling, pre-infusion mechanics, grinder-profile interaction, freshness | `agent-knowledge/EXTRACTION_SCIENCE.md` |
| Peak flavor windows, CO2 timeline, storage, buying timing | `agent-knowledge/BEAN_FRESHNESS_AND_STORAGE.md` |
| Decaf, blends, archetype patterns, special extraction adjustments | `agent-knowledge/SPECIAL_CATEGORIES.md` |
| Milk steaming, drink specs, single-boiler workflow, temp thresholds | `agent-knowledge/MILK_AND_DRINKS.md` |
| Basket types, dose rules, puck depth, ridgeless vs ridged | `agent-knowledge/BASKETS.md` |
| Ready-to-use profile templates, selection by taste goal or problem | `agent-knowledge/PROFILE_LIBRARY.md` |
| Profile JSON schema, phases, pump modes, stop conditions | `agent-knowledge/GAGGIMATE_PROFILE_CREATION_GUIDE.md` |

## Workflow

### 1. IDENTIFY the Question

Parse the user's question for the core topic. One question = one primary file + at most one supporting file.

### 2. LOAD the Right File(s)

Read the relevant file(s) from `agent-knowledge/`. Do not load files that aren't relevant to the question.

**Cascade prevention:** Maximum 1 primary file + 1 supporting file per question. If the answer requires more, split the question into parts and address them sequentially.

### 3. ANSWER from the File

Answer using the loaded knowledge file content. Cite the source:
> "Per `agent-knowledge/PRESSURE_GUIDE.md`: light washed coffees typically extract well at 8-9 bar..."

If the answer isn't in the knowledge files, say so explicitly and answer from general espresso knowledge with that caveat.

### 4. SUGGEST Follow-up Skills

If the question implies action:
- "How should I adjust my grind?" → suggest `/feedback` after next shot
- "What profile should I use?" → suggest `/gaggimate-profiles`
- "I'm starting a new coffee" → suggest `/new-coffee`

---

## Quick Reference

**User asks about temperature for light roasts:**
Load `ESPRESSO_BREWING_BASICS.md` → cite the temperature-by-roast table

**User asks why their shot tastes sour AND bitter:**
Load `ESPRESSO_TASTING_GUIDE.md` → cite the channeling rule (Scott Rao)

**User asks about pressure for an anaerobic natural:**
Load `PRESSURE_GUIDE.md` → cite the roast x processing matrix

**User asks about steaming technique:**
Load `MILK_AND_DRINKS.md` → cite the steaming workflow

**User asks about a specific profile pattern:**
Load `PROFILE_LIBRARY.md` → find matching profile template
