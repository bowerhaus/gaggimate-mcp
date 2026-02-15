---
name: diagnose
description: Analyze Gaggimate shot telemetry to diagnose extraction issues. Use when user shares shot data, asks about a specific shot ID, says "/diagnose", or wants to understand what the pressure/flow/temperature curves reveal about their extraction.
---

<command-name>diagnose</command-name>

# Shot Telemetry Diagnosis Skill

Analyze shot telemetry data to identify extraction problems and correlate pressure/flow/temperature curves with taste outcomes.

## Always Load (every invocation)

1. `user-setup.md` — basket size, grinder, active coffee
2. Active coffee's `coffees/{roaster}-{name}.md` — bean profile, processing, tasting history
3. `agent-knowledge/EXTRACTION_SCIENCE.md` — channeling patterns, pre-infusion mechanics, visual diagnosis

## Conditionally Load

| File | When |
|------|------|
| `desktop-app-skills/references/diagnose/TELEMETRY_PATTERNS.md` | Need specific pattern reference for anomalies |
| `desktop-app-skills/references/diagnose/DIAGNOSTIC_TREES.md` | Working through a complex multi-symptom diagnosis |
| `agent-knowledge/PRESSURE_GUIDE.md` | Pressure-related issues or profile style mismatch |
| `agent-knowledge/ESPRESSO_BREWING_BASICS.md` | Grind/ratio/temp adjustment guidance needed |

---

## Workflow

### 1. RETRIEVE Shot Data

If shot ID provided:
```
analyze_shot(shot_id=X)
```
```
list_recent_shots()
```

If no shot ID, ask the user for one or retrieve recent shots and ask which to analyze.

### 2. IDENTIFY the Coffee Context

- Check `user-setup.md` → Active Coffee
- Read `coffees/{roaster}-{name}.md` → bean profile (roast level, processing, altitude), recent tasting notes
- Cross-reference: what does the user expect from this coffee? What have previous shots tasted like?

### 3. ANALYZE Telemetry

Parse the shot data for:

**Pressure curve:**
- Pre-infusion phase: pressure ramp rate, peak, duration
- Main extraction: pressure stability, target vs actual
- Pressure spikes or drops (channeling indicators)

**Flow rate:**
- First drip time (resistance indicator)
- Flow acceleration pattern
- Sudden flow increases mid-shot (channeling)
- Declining flow late in shot (normal vs over-extracted)

**Temperature:**
- Temperature stability during extraction
- Deviation from target (offset)

**Weight/Volume:**
- BT scale artifact handling: ignore spikes, drops to 0g, or null readings near end-of-shot
- Estimate dose out from last stable weight sample, or `total_volume_ml x 0.82`
- Calculate actual ratio

**Time:**
- Total shot time
- Time to first drip
- Phase durations (if profiled shot)

### 4. CORRELATE with Taste

If tasting notes are available (from coffee file or user provides):
- Map telemetry anomalies to taste outcomes
- Confirm or update diagnosis from `/feedback` if cross-referencing

**Key correlations:**

| Telemetry Pattern | Likely Cause | Taste Impact |
|-------------------|-------------|--------------|
| Pressure spike early, then drop | Channeling started early | Sour AND bitter simultaneously |
| Slow first drip (>12s), high peak pressure | Grind too fine | Bitter, over-extracted |
| Fast first drip (<4s), low peak pressure | Grind too coarse | Sour, weak |
| Unstable flow mid-shot | Channeling | Uneven extraction |
| Temperature drop during extraction | Heat loss (single-boiler) | Under-extraction of temperature-sensitive compounds |
| Pressure never reaches target | Dose too light or grind too coarse | Watery, under-extracted |

### 5. DIAGNOSE & RECOMMEND

State clearly:
1. **What happened** — describe the telemetry in plain language
2. **Why it happened** — root cause (grind, puck prep, profile mismatch, dose, etc.)
3. **What to change** — specific actionable recommendation

**Adjustment hierarchy:**
1. Grind size (largest lever)
2. Dose / ratio
3. Puck prep (if channeling)
4. Temperature
5. Profile / pressure curve

**Channeling diagnosis (from EXTRACTION_SCIENCE.md):**
- Sudden mid-shot flow increase = channeling
- "Sour AND bitter" taste with normal time = channeling
- Fix: better puck prep (WDT, even distribution, level tamp). NOT grind finer.

### 6. SUGGEST Follow-up

- If the next step is a grind/ratio adjustment: direct to `/feedback` after next shot
- If a profile change is warranted: suggest `/gaggimate-profiles`
- If the pattern suggests a systematic setup issue: reference `user-setup.md` and ask about puck prep routine

---

## Output Format

```
## Shot Analysis: [Shot ID]

### Telemetry Summary
- **Pre-infusion:** [duration, peak pressure]
- **Main extraction:** [pressure range, stability]
- **Flow:** [first drip time, pattern description]
- **Time:** [total time, to target weight]
- **Estimated ratio:** [X:X.X] ([Xg in / ~Xg out])

### Diagnosis
[Plain-language explanation of what happened and why]

### Correlation with Taste
[How the telemetry explains the reported taste, if taste data available]

### Recommendation
**Primary:** [specific change]
**Why:** [reasoning]
**Backup:** [if primary doesn't resolve it]

### Next Shot
[What to watch for, what to expect if the change works]
```
