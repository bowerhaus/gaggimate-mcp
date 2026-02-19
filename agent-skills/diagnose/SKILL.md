---
name: diagnose
description: >
  Diagnose espresso extraction issues by correlating machine telemetry with taste feedback.
  Use when user says: "what went wrong", "analyze that shot", "why did it taste [sour/bitter/flat]",
  "my shots are inconsistent", or asks about pressure spikes, flow issues, or extraction problems.
  Fetches shot data via analyze_shot MCP tool, interprets patterns, and provides actionable recommendations.
---

# Espresso Diagnostic Skill

Diagnose espresso extraction issues by correlating Gaggimate telemetry data with taste feedback.

*Adapted from [gaggimate-barista](https://github.com/charleshall888/gaggimate-barista) by Charlie Hall.*

## Diagnostic Workflow

### 1. GATHER Information

**Required inputs:**
- Shot ID (from `list_recent_shots` if not provided)
- Taste feedback: sour, bitter, flat, astringent, balanced, or specific descriptors
- Any visual observations (channeling, spurting, blonde early, etc.)

**Fetch telemetry:**
```
Use: analyze_shot(shot_id)
```

**Fetch shot notes if available:**
```
Use: manage_shot_notes(shot_id, action="get")
```

### 1b. IDENTIFY Shot Style

Before analyzing, identify the shot style so you compare against the right expectations. Use three tiers of detection (try in order, use first that succeeds):

**Tier 1 — Fetch profile definition (preferred):**

If `analyze_shot` returns a `profile_id`, fetch the full profile:
```
Use: manage_profile(action="get", profile_id=<profile_id>)
```

Classify by phase structure:
- Has a phase with pump off (`"target": "power"` and `"pressure": 0`) → **Bloom**
- Flow-targeted extraction with flow >= 3.5 ml/s → **Turbo**
- Brew phase with pressure declining >= 4 bar over >= 15s → **Lever Decline**
- Extraction pressure <= 7 bar + high volumetric target (>= dose × 3.5) → **Allongé**
- Extraction pressure < 9 bar, no bloom, no decline → **Dark/Gentle**
- Default → **Classic 9-Bar**

**Tier 2 — Profile name keywords (fallback):**

Match `profile_name` from `analyze_shot`:
- Contains "turbo" → **Turbo**
- Contains "bloom", "natural bloom" → **Bloom**
- Contains "allongé", "allonge", "lungo" → **Allongé**
- Contains "lever", "decline" → **Lever Decline**
- Contains "gentle", "dark", "milk" → **Dark/Gentle**
- Otherwise → **Classic 9-Bar**

**Tier 3 — Telemetry fingerprint (last resort):**

See `references/TELEMETRY_PATTERNS.md` (Style Detection Fingerprints section).

### 2. ANALYZE Telemetry

**First, determine the final weight — NEVER ask the user.** The BT scale frequently produces artifacts: spikes, drops to 0g, or null readings near end-of-shot. Estimate dose out yourself:

**Weight estimation priority:**
1. **Last stable weight sample** — scan backward, skip drops to 0g or spikes >2× the inter-sample trend
2. **Flow meter total minus puck absorption** — use `total_volume_ml × 0.82` as fallback
3. **Interpolate from mid-shot weight + flow** — if you have a reliable weight mid-shot

State your estimated dose out and how you derived it, then move on. A ±2g estimate is fine.

**Load style-specific expectations** from `gaggimate://knowledge/PRESSURE_GUIDE.md` (Pressure by Shot Style) and `gaggimate://knowledge/PROFILE_LIBRARY.md` (Quick Reference table). Compare telemetry against style-specific ranges — not generic 9-bar ranges.

**Universal thresholds** (style-independent):

| Metric | Normal | Anomaly |
|--------|--------|---------|
| Temperature variance | ±1°C from target | >2°C = equipment instability |
| Pressure spike above profile target | — | >1.5 bar above = too fine / channeling |

Flag an anomaly only when a metric falls **outside the identified style's expected range**.

### 2b. COMPARE Intended vs Actual (when profile definition available)

| Comparison | Interpretation |
|------------|----------------|
| Pressure exceeded target by >1.5 bar | Grind too fine or dose too high |
| Pressure never reached target (>1.5 bar below) | Context-dependent: normal for post-bloom ramps, too coarse for non-bloom |
| Volumetric target reached much earlier than phase duration | Grind too coarse (flow too fast) |
| Volumetric target not reached within phase duration | Grind too fine (flow too slow) |
| Decline phase pressure stayed >1 bar above target floor | Grind too fine — high puck resistance |
| Flow during extraction well above/below profile's flow target | Grind mismatch for this style |

### 3. CORRELATE Taste with Telemetry

Cross-reference the user's taste feedback with telemetry patterns.

**See:** `references/TELEMETRY_PATTERNS.md` for detailed correlation matrix and `references/DIAGNOSTIC_TREES.md` for taste-based decision trees.

### 4. RECOMMEND Actions

Provide specific, prioritized recommendations:
1. **Primary adjustment** (most likely to fix the issue)
2. **Secondary adjustment** (if primary doesn't work)
3. **Profile consideration** (if extraction mechanics need changing)

Always explain WHY each recommendation addresses the diagnosed issue.

---

## Response Format

```
## Shot Analysis: [Shot ID]

### Identified Style: [Style Name]
(detected via [Tier 1: profile definition / Tier 2: profile name / Tier 3: telemetry fingerprint])

### Telemetry Summary
- **Pressure:** [peak] bar (style expects: X-Y bar)
- **Flow:** [avg] ml/s, first drip at [X]s (style expects: A-B ml/s)
- **Temperature:** [avg]°C (target: X°C, variance: ±X°C)
- **Timing:** [total]s total (style expects: E-Fs)

### Phase Comparison (if profile definition available)
[Intended vs actual for each phase — pressure, flow, timing]

### Diagnosis
[Correlation between telemetry and reported taste, interpreted through style-specific expectations]

### Recommendations
1. **[Primary fix]** — [specific action with reasoning]
2. **[Secondary fix]** — [backup if primary doesn't work]
3. **[Profile consideration]** — [if applicable]

### What to Watch For
[What user should observe on next shot to confirm diagnosis]
```
