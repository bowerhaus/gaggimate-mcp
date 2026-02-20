# Shot Diagnostics Reference

Comprehensive reference for all diagnostic metrics computed by `analyze_shot`.
Use this to understand what each metric means, how to interpret annotations,
and when to request which detail level.

---

## Detail Levels

The `analyze_shot` tool accepts a `detail` parameter:

| Level | When to use | Token cost | Includes |
|-------|-------------|------------|----------|
| **summary** (default) | Quick triage, first assessment | Lowest | Key indicators, phase list (no samples) |
| **per_phase** | Diagnosing specific phase issues | Medium | Full diagnostics + per-phase breakdowns + representative samples |
| **detailed** | Deep analysis, exact timing | Highest | Everything + all time-series samples |

**Start with `summary`.** Escalate to `per_phase` only when you need to know
*which phase* has the problem. Use `detailed` only when exact sample timings matter.

---

## Summary Level Diagnostics

Returned as a flat object with key indicators:

| Field | Type | What it tells you |
|-------|------|-------------------|
| `resistance_avg` | float | Average puck resistance (P/F²). Higher = finer grind or tighter puck. |
| `resistance_slope` | float | How resistance changes over the shot. Negative = erosion (normal). Steep negative = possible channeling. |
| `channeling_risk` | string | Overall channeling risk: LOW / MODERATE / HIGH / VERY_HIGH |
| `temperature_stability_c` | float | Std deviation of brew temp. Lower = more stable. |
| `pressure_rmse_bar` | float | RMSE between actual and target pressure (profile compliance). 0 = perfect adherence. |
| `max_overshoot_bar` | float | Largest pressure overshoot above target. >1.5 bar usually = grind too fine. |
| `scale_connected` | bool | Whether BT scale data was present. |
| `annotations` | dict | Human-readable labels for all of the above. |

### Summary Annotations

| Key | Bands |
|-----|-------|
| `resistance_level` | VERY_LOW (<0.5) · LOW (<1.5) · MODERATE (<3.0) · HIGH (<5.0) · VERY_HIGH |
| `resistance_erosion` | INCREASING (≥0.05) · FLAT (≥−0.02) · GRADUAL_DECLINE (≥−0.08) · MODERATE_DECLINE (≥−0.15) · STEEP_DECLINE |
| `channeling_risk` | LOW · MODERATE · HIGH · VERY_HIGH |
| `temperature_stability` | VERY_STABLE (<0.3) · STABLE (<0.8) · MODERATE (<1.5) · UNSTABLE |
| `pressure_adherence` | EXCELLENT (<0.3) · GOOD (<0.8) · FAIR (<1.5) · POOR |
| `pressure_overshoot` | WITHIN_TOLERANCE (<0.5) · SLIGHT_OVERSHOOT (<1.0) · MODERATE_OVERSHOOT (<1.5) · SIGNIFICANT_OVERSHOOT |

---

## Full Diagnostics (per_phase / detailed)

Returned as an object with these sub-sections:

### Resistance (Puck Resistance)

The **master diagnostic metric**. Computed as R = P / F² (quadratic Darcy model).
Captures grind fineness, puck prep quality, channeling, and erosion.

| Field | Unit | Meaning |
|-------|------|---------|
| `avg` | dimensionless | Average resistance across brew phase |
| `std` | dimensionless | Variability of resistance |
| `slope` | /s | Change rate — negative = erosion, steep negative = channeling |
| `peak` | dimensionless | Maximum resistance recorded |
| `peak_timing_pct` | 0–1 | When peak occurred (0 = start, 1 = end of brew) |

**Annotations:**

| Key | What it assesses | Bands |
|-----|------------------|-------|
| `level` | Grind fineness | VERY_LOW · LOW · MODERATE · HIGH · VERY_HIGH |
| `stability` | Puck consistency | VERY_STABLE (<0.2) · STABLE (<0.5) · MODERATE (<1.0) · VOLATILE |
| `erosion` | Puck degradation | INCREASING · FLAT · GRADUAL_DECLINE · MODERATE_DECLINE · STEEP_DECLINE |
| `saturation` | Peak timing | EARLY (<0.15) · GOOD_TIMING (<0.35) · MID_SHOT (<0.60) · LATE |

**Diagnostic patterns:**
- High avg + STEEP_DECLINE slope → grind too fine, channeling developing
- Low avg + INCREASING slope → grind too coarse, under-extraction
- VOLATILE stability → inconsistent puck prep or channeling
- EARLY peak → puck saturated before brew got going

### Channeling Indicators

Detects channeling from pressure/flow volatility.

| Field | Unit | Meaning |
|-------|------|---------|
| `pressure_volatility_bar` | bar | Std dev of brew pressure |
| `flow_volatility_ml_s` | ml/s | Std dev of brew flow |
| `pressure_max_drop_rate_bar_s` | bar/s | Steepest pressure drop (most negative) |
| `flow_acceleration_late_ml_s2` | ml/s² | Flow acceleration in last 40% of brew |
| `overall_risk` | string | Combined risk assessment |

**Annotations:**

| Key | Bands |
|-----|-------|
| `pressure_stability` | VERY_STABLE (<0.15) · STABLE (<0.35) · MODERATE_JITTER (<0.6) · JITTERY (<1.0) · VOLATILE |
| `flow_stability` | VERY_STABLE (<0.10) · STABLE (<0.25) · MODERATE_JITTER (<0.50) · JITTERY (<0.80) · VOLATILE |
| `pressure_drop` | NORMAL (≥−0.5) · MODERATE_DROP (≥−1.5) · STEEP_DROP (≥−3.0) · CLIFF |
| `late_flow_trend` | STABLE (<0.02) · SLIGHT_ACCELERATION (<0.05) · MODERATE_ACCELERATION (<0.10) · RAPID_ACCELERATION |

**Risk scoring:** Scoring adds points for high pressure volatility, high flow volatility,
steep pressure drops, and late flow acceleration. ≤1 = LOW, ≤3 = MODERATE, ≤5 = HIGH, >5 = VERY_HIGH.

### Temperature Diagnostics

Temperature stability vs target during brew.

| Field | Unit | Meaning |
|-------|------|---------|
| `overshoot_c` | °C | Maximum temperature above target |
| `undershoot_c` | °C | Maximum temperature below target |
| `stability_std_c` | °C | Std dev of brew temperature |

**Annotations:**

| Key | Bands |
|-----|-------|
| `overshoot` / `undershoot` | MINIMAL (<0.5) · SLIGHT (<1.5) · MODERATE (<3.0) · SIGNIFICANT |
| `stability` | VERY_STABLE (<0.3) · STABLE (<0.8) · MODERATE (<1.5) · UNSTABLE |

### Extraction Metrics

Brew quality indicators.

| Field | Unit | Meaning |
|-------|------|---------|
| `pressure_auc_bar_s` | bar·s | Area under pressure curve (total energy delivered) |
| `pressure_slope_brew_bar_s` | bar/s | Pressure trend during brew |
| `flow_slope_brew_ml_s2` | ml/s² | Flow trend during brew |
| `flow_avg_brew_ml_s` | ml/s | Average flow during brew |

**Annotations:**

| Key | Values |
|-----|--------|
| `pressure_trend` | INCREASING · FLAT · GRADUAL_DECLINE · MODERATE_DECLINE · STEEP_DECLINE |
| `flow_trend` | DECLINING / STABLE / INCREASING |

### Weight / Yield Diagnostics

From BT scale data (when available).

| Field | Unit | Meaning |
|-------|------|---------|
| `rate_avg_g_s` | g/s | Average weight accumulation rate |
| `rate_std_g_s` | g/s | Variability of accumulation rate |
| `scale_connected` | bool | Whether scale data was present |

If `scale_connected` is false, `rate_avg_g_s` and `rate_std_g_s` will be null.

### Profile Compliance

Measures how well the machine followed the programmed target profile.
**Only available when target pressure (tp) data is in the shot.**

| Field | Unit | Meaning |
|-------|------|---------|
| `pressure_rmse_bar` | bar | RMSE between actual and target pressure |
| `flow_rmse_ml_s` | ml/s | RMSE between actual and target flow (null if no tf data) |
| `max_pressure_overshoot_bar` | bar | Largest single overshoot above target |
| `max_pressure_undershoot_bar` | bar | Largest single undershoot below target |

**Annotations:**

| Key | Bands |
|-----|-------|
| `pressure_adherence` | EXCELLENT (<0.3) · GOOD (<0.8) · FAIR (<1.5) · POOR |
| `pressure_overshoot` | WITHIN_TOLERANCE (<0.5) · SLIGHT_OVERSHOOT (<1.0) · MODERATE_OVERSHOOT (<1.5) · SIGNIFICANT_OVERSHOOT |
| `flow_adherence` | Same as pressure_adherence (only present when tf data available) |

**Key diagnostic insight:** `max_pressure_overshoot_bar > 1.5` is a strong signal
that the grind is too fine — the machine cannot push enough water through the puck,
so pressure builds beyond what the profile targets. Recommend coarsening grind.

---

## Per-Phase Diagnostics

At `per_phase` and `detailed` levels, each phase in the `phases` list includes a
`diagnostics` object with metrics specific to that phase type.

### Phase Classification

Phase names from the firmware are classified automatically:

| Phase Type | Matched Names |
|------------|---------------|
| **preinfusion** | preinfusion, pre-infusion, pi, soak, bloom, fill, preinfuse |
| **decline** | decline, taper, ramp-down, ramp down, cool down, cooldown |
| **brew** | Everything else (extraction, brew, main, hold, flat, step N, etc.) |

### Common Fields (all phase types)

| Field | Meaning |
|-------|---------|
| `phase_type` | "preinfusion" / "brew" / "decline" |
| `avg_pressure_bar` | Average pressure in this phase |
| `avg_flow_ml_s` | Average flow in this phase |
| `pressure_rmse_bar` | RMSE vs target pressure for this phase |
| `flow_rmse_ml_s` | RMSE vs target flow for this phase |
| `annotations.pressure_adherence` | EXCELLENT / GOOD / FAIR / POOR |

### Preinfusion-Specific Fields

| Field | Unit | Meaning |
|-------|------|---------|
| `ramp_rate_bar_s` | bar/s | How fast pressure ramps up |
| `saturation_time_s` | s | Time until flow stabilises (puck saturation) |

**Annotations:** `ramp_rate` → VERY_SLOW (<0.5) · SLOW (<1.5) · NORMAL (<3.0) · FAST (<5.0) · VERY_FAST

### Brew-Specific Fields

| Field | Unit | Meaning |
|-------|------|---------|
| `resistance_avg` | dimensionless | Puck resistance in this phase |
| `resistance_slope` | /s | Resistance trend in this phase |
| `channeling_risk` | string | Channeling risk for this phase |
| `pressure_stability_bar` | bar | Pressure volatility |
| `flow_stability_ml_s` | ml/s | Flow volatility |

**Annotations:** `resistance_level`, `resistance_erosion`, `channeling`, `pressure_stability`, `flow_stability`

### Decline-Specific Fields

| Field | Unit | Meaning |
|-------|------|---------|
| `taper_rate_bar_s` | bar/s | Rate of pressure decline (negative values) |
| `taper_smoothness` | bar/s | Std dev of pressure derivatives — lower = smoother taper |

**Annotations:** `taper_smoothness` → VERY_SMOOTH (<0.2) · SMOOTH (<0.5) · MODERATE (<1.0) · ROUGH

---

## Interpretation Cheat Sheet

### Grind Too Fine
- `max_pressure_overshoot_bar` > 1.5 (MODERATE/SIGNIFICANT_OVERSHOOT)
- Resistance avg HIGH or VERY_HIGH
- Flow avg below expected for style
- Channeling risk may be elevated

### Grind Too Coarse
- Pressure never reaches target (`max_pressure_undershoot_bar` high)
- Resistance avg LOW or VERY_LOW
- Flow avg above expected for style
- Fast extraction time

### Channeling
- `channeling_risk` HIGH or VERY_HIGH
- Resistance slope STEEP_DECLINE
- Pressure volatility JITTERY or VOLATILE
- Flow acceleration in late shot

### Temperature Problems
- `stability_std_c` > 1.5 (UNSTABLE) → equipment issue
- `overshoot_c` > 3.0 → thermosiphon or PID issue
- `undershoot_c` > 3.0 → machine not heated properly

### Good Shot Indicators
- Resistance MODERATE, STABLE, GRADUAL_DECLINE
- Channeling LOW
- Temperature VERY_STABLE or STABLE
- Profile adherence EXCELLENT or GOOD
- Overshoot WITHIN_TOLERANCE

---

## Detail Level Strategy

```
User says "what's wrong with my shot?"
  → analyze_shot(shot_id)              # summary first

Summary shows HIGH channeling risk?
  → analyze_shot(shot_id, detail="per_phase")  # which phase?

Per-phase shows brew phase channeling?
  → Correlate with taste, recommend grind adjustment

Need exact timing of a pressure spike?
  → analyze_shot(shot_id, detail="detailed")   # all samples
```
