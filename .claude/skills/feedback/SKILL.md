---
name: feedback
description: >
  Gather shot feedback, analyze extraction, recommend adjustments, and record results.
  Use when user says: "/feedback", "I just pulled a shot", "how was that", "it tasted [sour/bitter/flat/good]",
  provides a star rating, shares taste observations, or asks "what should I adjust" after a shot.
  Owns the full shot feedback loop: gathering, analysis, grind map updates, tasting notes, and drink format.
---

<command-name>feedback</command-name>

# Shot Feedback & Dialing Skill

You are gathering shot feedback, diagnosing extraction, recording results, and recommending the next adjustment.

## Always Load (every invocation)

Read these files before proceeding:
1. `user-setup.md` — active coffee, basket size, grinder
2. Active coffee's `coffees/{roaster}-{name}.md` — recent tasting notes, profiles, bean profile
3. `agent-knowledge/ESPRESSO_BREWING_BASICS.md` — adjustment strategies, diagnostic decision tree
4. `agent-knowledge/ESPRESSO_TASTING_GUIDE.md` — sour vs bitter diagnosis, tasting methodology

## Conditionally Load

| File | When |
|------|------|
| `agent-knowledge/PRESSURE_GUIDE.md` | Feedback suggests pressure/profile style change |
| `agent-knowledge/MILK_AND_DRINKS.md` | User asks about drink format, or shot is dialed in (4+ balanced) and user has milk drink preferences |
| `grind-map.md` | Rating 4-5 stars AND grind setting provided |

---

## Workflow

### 1. GATHER Context

- Read `user-setup.md` → Active Coffee section
- If set: read the coffee's `coffees/{roaster}-{name}.md` (bean profile, processing, recent tasting notes)
- If not set: ask the user what coffee they're brewing before proceeding
- **Stale check:** If roast date is 30+ days old, gently ask if user is still on this bag

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
2. `total_volume_ml x 0.82` (puck absorption estimate)
3. User's stated ratio x dose in

A +/-2g estimate is fine for diagnosis and recording.

### 3. ANALYZE & RECOMMEND

Use the loaded knowledge files (BREWING_BASICS + TASTING_GUIDE) to diagnose and recommend.

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
| **Sour AND bitter** | **Channeling** | **Fix puck prep (WDT, distribution, even tamp). NOT grind.** |
| Balanced but flat | Under-developed | Increase temp 1 degree C, or try longer ratio |
| Balanced but thin | Low body | Shorter ratio, or finer grind |

**The "sour AND bitter" rule (Scott Rao):** When a shot tastes both sour and bitter simultaneously, water is finding paths of least resistance. The fix is puck prep, not grind. Grinding finer when channeling is present makes it worse.

Always explain *why* you're suggesting a change. One primary recommendation, one backup.

### 4. RECORD (silent, no confirmation needed)

Do all of these automatically after feedback is collected:

#### 4a. Tasting Notes

Append a row to the Tasting Notes table in the active coffee's `coffees/{roaster}-{name}.md`:

| # | Date | Shot | Grind | In/Out | Ratio | Profile | Balance | Stars | Observations |
|---|------|------|-------|--------|-------|---------|---------|-------|--------------|

- **#**: Sequential shot number for this coffee
- **Date**: Compact format (e.g., Feb 12)
- **Shot**: Gaggimate shot ID (6-digit, for `/diagnose` cross-reference)
- **In/Out**: Dose in/out as "22/48g"
- **Ratio**: Actual ratio as 1:X.X
- **Profile**: Short profile style name
- **Balance**: Sour / Balanced / Bitter
- **Observations**: Brief sensory notes (5-10 words)

#### 4b. Grind Map (successes only)

Trigger: rating 4-5 stars AND grind setting provided AND coffee is known.

1. Read `grind-map.md`
2. Append row: Coffee, Roast, Process, Origin, Days Off Roast, Grind, Profile, Ratio, Temp, Rating, Date

#### 4c. Shot Notes to Device

If a shot ID is available, sync feedback:
```
manage_shot_notes(shot_id, action="update", rating=X, balance_taste="...", notes="...", grind_setting="...", dose_in=X, dose_out=X)
```

### 5. SUGGEST Next Steps

**If still dialing in (rating < 4 or not balanced):**
- State the specific change for the next shot
- Explain what to watch for

**If dialed in (rating 4+ AND balanced):**
- Celebrate briefly
- Recommend drink format:

| Shot Character | Recommended Format |
|----------------|-------------------|
| Bright, fruity, delicate | Cortado or piccolo |
| Sweet, balanced, medium body | Cappuccino or flat white |
| Intense, heavy body | Latte |
| Clarity-focused, tea-like | Cortado or piccolo |

If user wants milk science or drink recipes, load `agent-knowledge/MILK_AND_DRINKS.md`.

---

## Integration with Other Skills

- Deeper shot telemetry analysis: suggest `/diagnose`
- Profile modifications: suggest `/gaggimate-profiles`
- New coffee: suggest `/new-coffee`
