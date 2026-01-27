---
name: gaggimate-profiles
description: Create custom espresso extraction profiles for Gaggimate-equipped machines (Gaggia Classic, Gaggia Classic Pro, Gaggia Classic Evo, Rancilio Silvia, DeLonghi ECP). Use when designing pressure profiles, flow profiles, blooming profiles, lever simulation profiles, or helping with espresso extraction settings and troubleshooting. Also use when the user mentions Gaggimate, espresso profiles, pressure profiling, or extraction settings.
metadata:
  author: julianleopold
  version: "1.0"
---

## When to use this skill

Use this skill when asked to:
- Create new espresso extraction profiles for Gaggimate machines
- Modify or troubleshoot existing Gaggimate profiles
- Design pressure profiles, flow profiles, or blooming profiles
- Help with espresso extraction issues (channeling, over-extraction, under-extraction)
- Explain profile concepts like pressure profiling, flow control, transitions
- Suggest profiles for specific coffee types or roast levels

## How to use this skill

When creating profiles:

1. **Gather information** (if not provided):
   - Coffee type/origin and roast level
   - Dose amount (typically 18g for double shot)
   - Desired output ratio (1:2 is classic)
   - Flavor goals (more body, more acidity, reduce bitterness, etc.)
   - Whether they have a Bluetooth scale (for volumetric stop)

2. **Select appropriate pattern**:
   - Light roasts → Bloom profile with higher temp (94-96°C)
   - Medium roasts → Classic 9-bar or slight decline (92-94°C)
   - Dark roasts → Lower pressure (7-8 bar) with decline (88-90°C)
   - Lever simulation → Declining pressure profile

3. **Load the reference file** for complete documentation:
   - `references/profile-guide.md` - Complete JSON schema, examples, and troubleshooting

4. **Generate complete JSON** with all required fields

5. **Explain the profile** - describe what each phase does and why

## Quick Reference

### Profile Structure

```json
{
  "label": "Profile Name",
  "type": "pro",
  "description": "Optional description",
  "temperature": 93,
  "phases": [...]
}
```

### Phase Structure

Each phase needs:
- `name`: Display name (e.g., "Pre-infusion", "Ramp", "Hold")
- `phase`: Category - `"preinfusion"`, `"brew"`, or `"decline"`
- `valve`: `1` (open) or `0` (closed) - almost always `1`
- `duration`: Max seconds (1-60)
- `temperature`: Override global temp (`0` = use global)
- `transition`: Object with `type`, `duration`, `adaptive`
- `pump`: Object with `target`, `pressure`, `flow`
- `targets`: Optional array of stop conditions

### Pump Modes

```json
// Pressure mode - maintain specific pressure
"pump": { "target": "pressure", "pressure": 9, "flow": 4 }

// Flow mode - maintain specific flow rate
"pump": { "target": "flow", "pressure": 9, "flow": 2.5 }

// Adaptive flow - auto-adjust to puck resistance
"pump": { "target": "flow", "pressure": 9, "flow": -1 }

// Power mode (for bloom - pump off)
"pump": { "target": "power", "pressure": 0, "flow": 0 }
```

### Transition Types

| Type | Use Case |
|------|----------|
| `instant` | Phase starts, step changes |
| `linear` | Standard pressure ramps |
| `ease-in` | Gentle pre-infusion to extraction |
| `ease-out` | Tapering at end of shot |
| `ease-in-out` | Complex profiles, most natural |

### Stop Conditions (Targets)

```json
"targets": [
  { "type": "volumetric", "operator": "gte", "value": 36 }
]
```

Types: `volumetric` (grams), `water_pumped` (ml), `pressure` (bars), `flow` (ml/s)
Operators: `gte` (≥), `lte` (≤), `gt` (>), `lt` (<)

### Temperature Guidelines

| Roast Level | Temperature |
|-------------|-------------|
| Light (Nordic) | 94-96°C |
| Medium (City) | 92-94°C |
| Medium-dark (Vienna) | 90-92°C |
| Dark (French/Italian) | 88-90°C |

### Common Profile Patterns

**Classic 9-Bar (Medium Roasts):**
1. Pre-infusion: 4s, flow mode at 3 ml/s
2. Ramp: 4s, linear transition to 9 bar
3. Hold: 25s at 9 bar, stop at target weight

**Bloom Profile (Light Roasts):**
1. Fill: 5s, flow at 2.5 ml/s
2. Bloom: 8s, pump off (power mode, pressure 0)
3. Ramp: 5s, ease-in-out to 9 bar
4. Hold: 20s at 9 bar, stop at target weight

**Lever Simulation:**
1. Pre-infusion: 5s, flow at 3 ml/s
2. Peak: 5s ramp to 9 bar
3. Decline: 30s linear decline from 9 to 3 bar

## Output Requirements

When generating profiles:
1. **Always output complete, valid JSON** that can be directly imported
2. **Include all required fields** - don't omit any phase properties
3. **Use sensible defaults** - valve: 1, adaptive: true for most cases
4. **Add a volumetric target** on the final extraction phase
5. **Explain your choices** after the JSON

## Keywords

Gaggimate, espresso profile, pressure profile, flow profile, extraction, pre-infusion, bloom, lever simulation, Gaggia Classic, Gaggia Classic Pro, Gaggia Classic Evo, Rancilio Silvia, DeLonghi ECP, coffee extraction, temperature profiling
