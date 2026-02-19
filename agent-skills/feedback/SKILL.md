---
name: feedback
description: >
  Gather shot feedback, analyze extraction, recommend adjustments, and record results.
  Use when user says: "/feedback", "I just pulled a shot", "how was that", "it tasted [sour/bitter/flat/good]",
  provides a star rating, shares taste observations, or asks "what should I adjust" after a shot.
  Owns the full shot feedback loop: gathering, analysis, tasting notes, and drink format.
---

# Shot Feedback & Dialing Skill

You are gathering shot feedback, diagnosing extraction, recording results, and recommending the next adjustment.

> Adapted from [gaggimate-barista](https://github.com/charleshall888/gaggimate-barista) by Charlie Hall.

## Context

Knowledge files are available on-demand via MCP resources. Load only what's needed:
- `gaggimate://knowledge/ESPRESSO_BREWING_BASICS.md` — adjustment strategies, diagnostic decision tree, variable hierarchy
- `gaggimate://knowledge/ESPRESSO_TASTING_GUIDE.md` — sour vs bitter diagnosis, tasting methodology
- `gaggimate://knowledge/PRESSURE_GUIDE.md` — when feedback suggests pressure/profile style change
- `gaggimate://knowledge/MILK_AND_DRINKS.md` — when shot is dialed in and user wants drink recommendations

---

## Workflow

### 1. GATHER Context

- Read `gaggimate://user/setup` to load the user's equipment, basket size, and preferences.
- Read `gaggimate://coffees` to check for existing coffee tracking files, then load the relevant one via `gaggimate://coffees/{name}`.
- If no coffee context exists: ask the user what coffee they're brewing before proceeding.
- **Stale check:** If roast date is 30+ days old, gently ask if user is still on this bag.

### 2. COLLECT Feedback

Gather from the user (ask for what's missing):

| Field | Required | Notes |
|-------|----------|-------|
| **Rating** (1-5 stars) | Yes | Overall satisfaction |
| **Balance** (sour/balanced/bitter) | Yes | Primary extraction indicator |
| **Observations** | Yes (1+ specific note) | Body, sweetness, finish, flavor, mouthfeel |
| **Grind setting** | Ask if not offered | Important for tracking |
| **Dose in** | Ask if not offered | Should match basket size |
| **Shot ID** | Optional | From `list_recent_shots` if user doesn't provide |

**Minimum viable feedback:** Rating + balance + one specific observation.

**Weight estimation — NEVER ask the user for cup weight.** The BT scale often produces artifacts (spikes, drops to 0g, null readings). Estimate dose out from:
1. Last stable weight sample from telemetry (if shot ID available)
2. `total_volume_ml × 0.82` (puck absorption estimate)
3. User's stated ratio × dose in

A +/-2g estimate is fine for diagnosis and recording.

### 3. ANALYZE & RECOMMEND

Use the knowledge files (BREWING_BASICS + TASTING_GUIDE) to diagnose and recommend.

**Adjustment hierarchy** — adjust in this order:
1. **Grind size** — largest effect on extraction
2. **Yield/Ratio** — quick correction (5g rule)
3. **Temperature** — fine-tuning after grind is close
4. **Pressure/Profile** — style change or enhancement
5. **Puck prep** — channeling, inconsistency

**Critical diagnostic rules:**

| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Sour + fast (<20s) | Under-extracted, grind too coarse | Grind finer |
| Sour + normal time | Under-extracted at correct flow | Increase yield by 5g, then temp |
| Sour + slow (>35s) | Channeling likely | Better puck prep, longer pre-infusion |
| Bitter + slow (>35s) | Over-extracted, grind too fine | Grind coarser |
| Bitter + normal time | Over-extracted at correct flow | Decrease yield by 5g, then temp |
| **Sour AND bitter** | **Channeling** — uneven extraction | **Fix puck prep (WDT, distribution, even tamp). NOT grind.** |
| Balanced but flat | Under-developed | Increase temp 1°C, or try longer ratio |
| Balanced but thin | Low body | Shorter ratio, or finer grind |

**The "sour AND bitter" rule (Scott Rao):** When a shot tastes both sour and bitter simultaneously, water is finding paths of least resistance — over-extracting some grounds while under-extracting others. The fix is puck prep, not grind. Grinding finer when channeling is present makes it worse.

Always explain *why* you're suggesting a change. One primary recommendation, one backup.

### 4. RECORD

Do all of these automatically after feedback is collected:

#### 4a. Shot Notes → Device (via MCP)

If a shot ID is available, sync feedback to the device:
```
manage_shot_notes(shot_id, action="update", rating=X, balance_taste="...", notes="...", grind_setting="...", dose_in=X, dose_out=X)
```

#### 4b. Coffee Tracking (via MCP)

Log the shot to the coffee's tracking file:
```
manage_coffee(action="log_shot", name="[coffee-name]", shot_number=X, date="YYYY-MM-DD", rating=X, balance="[sour/balanced/bitter]", grind_setting="X", dose_in=X, dose_out=X, ratio="1:X", profile="[name]", notes="[observations]", adjustment="[what to change next]")
```

If no coffee tracking file exists yet, create one first:
```
manage_coffee(action="create", name="[coffee-name]", roaster="...", origin="...", process="...", roast_level="...", ...)
```

#### 4c. Grind Map (if 4+ stars)

**If 4+ stars AND grind setting provided**, add to the grind map:
```
manage_grind_map(action="add_entry", coffee="[name]", roast="[level]", process="[method]", grind="[setting]", profile="[name]", ratio="1:X", temp="X°C", rating="X/5", date="YYYY-MM-DD")
```

### 5. SUGGEST Next Steps

Based on the analysis:

**If still dialing in (rating < 4 or not balanced):**
- State the specific change for the next shot
- Explain what to watch for ("Time to first drip should increase" / "Look for more body")

**If dialed in (rating 4+ AND balanced):**
- Celebrate briefly
- Recommend a drink format based on shot character:

| Shot Character | Recommended Format |
|----------------|-------------------|
| Bright, fruity, delicate | Cortado or piccolo |
| Sweet, balanced, medium body | Cappuccino or flat white |
| Intense, heavy body | Latte |
| Clarity-focused, tea-like | Cortado or piccolo |

**Core principle:** Extract for the bean's best expression first, then match the drink format. Never adjust grind/ratio/pressure/temp to "make the shot work in milk."

If user wants full milk science, steaming technique, or drink recipes → reference MILK_AND_DRINKS.md knowledge file.

---

## Integration with Other Skills

- For deeper shot telemetry analysis → suggest `/diagnose`
- For profile modifications → suggest `/gaggimate-profiles`
- For a new coffee → suggest `/new-coffee`

---

## Quick Reference

**User says:** "3 stars, sour, grind 12, 22g in"
**Action:** Gather context → record via MCP → diagnose (sour = extract more) → recommend grind/yield change → update Coffee Tracking if present

**User says:** "5 stars, balanced, amazing sweetness"
**Action:** Gather context → celebrate → record via MCP → suggest adding to Coffee Tracking grind map → recommend drink format

**User says:** "it was sour AND bitter"
**Action:** Gather context → diagnose **channeling** → recommend puck prep fix, NOT grind change → record
