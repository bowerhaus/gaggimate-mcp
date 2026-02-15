---
name: new-coffee
description: >
  Research a new coffee bean and propose starting extraction parameters.
  Use when: (1) user shares a new bag of coffee (photo, name, or description),
  (2) user says "/new-coffee", "new beans", "dialing in a new coffee",
  (3) user asks "where should I start with this coffee".
  Accepts bag photos (extracts info via vision) or text descriptions.
  Researches origin, process, roast level via web search, checks grind-map.md
  for similar coffees, then recommends temperature, grind, ratio, and profile.
---

<command-name>new-coffee</command-name>

# New Coffee Research Skill

Systematically research a coffee and propose starting extraction parameters.

## Reference Files

Load on demand:
- `desktop-app-skills/references/new-coffee/RESEARCH_CHECKLIST.md` — detailed research patterns and web search guidance

## Workflow

### 1. GATHER Coffee Info

**If photo provided:**
- Extract from label: roaster, coffee name, origin, roast date, tasting notes
- Note any visible processing info (washed, natural, etc.)

**If text provided:**
- Parse roaster and coffee name
- Ask for roast date if not mentioned

### 2. RESEARCH via Web Search

Search for the specific coffee to find:
- Processing method (washed, natural, honey, anaerobic)
- Origin details (country, region, altitude if available)
- Variety (Bourbon, Gesha, Caturra, etc.)
- Roast level (light, medium, dark) — infer from tasting notes if not stated
- Roaster's tasting notes

Capture research synthesis: note flavor implications of origin, variety, processing, and altitude. These insights get saved to the coffee file's "What to Expect" section.

See `desktop-app-skills/references/new-coffee/RESEARCH_CHECKLIST.md` for detailed research patterns.

### 3. CONSULT Grind Map

Read `grind-map.md` and find similar coffees:
- Match by: roast level > processing method > origin
- Consider profile style compatibility: a grind from a bloom at 7.5 bar won't translate to a turbo at 6 bar. Show the user Profile, Ratio, and Temp columns so they see the full context.
- If match found: use as starting point, adjust for freshness and profile style differences
- If no match: recommend a starting point from `agent-knowledge/ESPRESSO_BREWING_BASICS.md` defaults

**Freshness adjustment:** Fresher beans (fewer days off roast) need coarser grind — CO2 adds puck resistance. If historical match was at 14 days and new bag is 7 days, suggest 1-2 steps coarser.

### 4. SYNTHESIZE Recommendations

Build recommendations using:
- **Temperature:** From `agent-knowledge/ESPRESSO_BREWING_BASICS.md` roast guidelines
- **Grind:** From grind-map match or brewing basics defaults
- **Ratio:** From processing method patterns
- **Pressure:** From `agent-knowledge/PRESSURE_GUIDE.md` roast x processing matrix
- **Profile:** From `agent-knowledge/PROFILE_LIBRARY.md` by roast/process
- **Dose:** From `user-setup.md` basket size — dose = basket size, don't underdose
- **Volumetric target:** Confirm profile's volumetric stop matches dose x ratio

### 5. CONFIRM with User

Before finalizing, ask:
> "This [process] [origin] typically shines with [approach]. Would you like to start there, or prefer a more conservative/adventurous approach?"

Options to offer:
- **Conservative:** Classic profile, standard ratio
- **Recommended:** Profile matched to bean characteristics (roast, process, intensity)
- **Adventurous:** Bloom profile or turbo shot if appropriate

### 6. UPLOAD Profile (if requested)

```
manage_profile(action="create", profile_name="[Coffee Name] [AI]", temperature=X, phases=[...])
```

Always add `[AI]` suffix to profile names.

### 7. SAVE Coffee File

Save research to a flat markdown file:

**File path:** `coffees/{roaster}-{coffee-name}.md` (kebab-case, e.g., `coffees/onyx-ethiopia-bochesa.md`)

If this coffee was bought before, read the existing file and update it (add new roast date, update freshness notes, append to Profiles if a new profile was created).

**Template:**

```markdown
# {Roaster} {Coffee Name}

## Bean Profile

| Field | Value |
|-------|-------|
| **Roaster** | ... |
| **Origin** | ... |
| **Process** | ... |
| **Roast Level** | ... |
| **Variety** | ... |
| **Altitude** | ... |
| **Tasting Notes** | {roaster's published tasting notes} |
| **Roast Date** | ... |

## What to Expect

{2-3 sentence summary of the coffee's character and what makes it interesting for espresso.}

- **Origin character:** {What this origin typically brings}
- **Processing ({method}):** {How processing affects flavor and why we chose this profile style}
- **Density/Altitude:** {If notable (1800+ masl), implications for grind and temp}

## Profiles

| Profile | Style | Temp | Pressure | Ratio | Notes |
|---------|-------|------|----------|-------|-------|

## Tasting Notes

| # | Date | Shot | Grind | In/Out | Ratio | Profile | Balance | Stars | Observations |
|---|------|------|-------|--------|-------|---------|---------|-------|--------------|
```

Remove `.gitkeep` from `coffees/` if it exists once real content is present. No confirmation needed.

### 8. Set Active Coffee

Update the Active Coffee section in `user-setup.md`:
- **Coffee**: Full coffee name
- **Directory**: Path to the coffee file (e.g., `coffees/onyx-ethiopia-bochesa.md`)
- **Roast Date**: From bag info, or "—" if unknown

No confirmation needed.

---

## Output Format

```
## Coffee Research: [Name]

### Bean Profile
- **Roaster:** [roaster]
- **Origin:** [country, region]
- **Process:** [washed/natural/honey/anaerobic]
- **Roast Level:** [light/medium/dark]
- **Variety:** [if known]
- **Tasting Notes:** [from roaster]
- **Days Off Roast:** [X days, or "unknown"]

### Similar Coffees in Your History
[Table from grind-map.md matches, or "No similar coffees yet"]

### Recommended Starting Parameters
| Parameter | Value | Reasoning |
|-----------|-------|-----------|
| Temperature | X degrees C | [roast level rationale] |
| Grind | XY | [from history or default, freshness adjusted] |
| Ratio | 1:X | [process rationale] |
| Profile | [name] | [why this profile] |
| Dose | Xg in to Xg out | [basket size rationale] |

### Saved To
`coffees/{roaster}-{coffee-name}.md`
Set as active coffee in `user-setup.md`

### What to Watch For
- [Specific guidance for first shot based on bean characteristics]
- [What taste outcomes to expect]
- [When to adjust and in which direction]
```
