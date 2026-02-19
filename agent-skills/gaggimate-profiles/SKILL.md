---
name: gaggimate-profiles
description: Create custom espresso extraction profiles for Gaggimate-equipped machines (Gaggia Classic Pro, Gaggia Classic Evo, Rancilio Silvia). Use when designing pressure profiles, flow profiles, blooming profiles, lever simulation profiles, or helping with espresso extraction settings and troubleshooting. Also use when the user mentions Gaggimate, espresso profiles, pressure profiling, or extraction parameters.
---

# Gaggimate Profile Creation Skill

Create custom espresso extraction profiles for Gaggimate-equipped machines. Gaggimate supports **Simple** and **Pro** profile types, with Pro profiles offering pressure profiling, flow control, and complex transitions.

> Enriched with patterns from [gaggimate-barista](https://github.com/charleshall888/gaggimate-barista) by Charlie Hall.

## Workflow

### Step 1: Gather Information

If not provided, read `gaggimate://user/setup` to load the user's equipment, basket size, and preferences. Ask about anything still missing:
- Coffee type/origin and roast level
- **Processing method** (washed, natural, honey, anaerobic — affects target pressure)
- Dose amount (**dose = basket size**; don't underdose)
- Desired output ratio (1:2 is classic)
- Flavor goals (more body, more acidity, reduce bitterness, etc.)
- Whether they have a Bluetooth scale (for volumetric stop conditions)

### Step 2: Select Profile Pattern

Load the relevant knowledge files via MCP resources to determine settings:
- **Temperature**: `gaggimate://knowledge/ESPRESSO_BREWING_BASICS.md` → "Temperature Guidelines by Roast"
- **Pressure**: `gaggimate://knowledge/PRESSURE_GUIDE.md` → roast × processing matrix
- **Profile pattern**: `gaggimate://knowledge/PROFILE_LIBRARY.md` → select by roast, process, and style

Quick reference for common patterns:

| Coffee Type | Temperature | Pressure | Profile Pattern |
|-------------|-------------|----------|-----------------|
| Light roasts (Ethiopia, Kenya) | 94-96°C | 6-8 bar | Bloom profile |
| Medium roasts (Colombia, Brazil) | 92-94°C | 8-9 bar | Classic 9-bar |
| Medium-dark (Vienna) | 90-92°C | 8-9 bar | Slight decline |
| Dark roasts (French/Italian) | 88-90°C | 7-8 bar | Low pressure with decline |
| Natural process (any roast) | Per roast | -1 bar from washed | Bloom or longer pre-infusion |

### Step 3: Load Reference Files (conditionally)

**Default: load ZERO reference files.** Steps 2 + 4 (knowledge files + inline JSON template) are sufficient for standard profiles built from library patterns. Only load a reference file when a specific trigger applies.

**Stop rule:** Load at most **2 reference files** per profile creation session.

| Reference | Load ONLY when... |
|-----------|--------------------|
| [EXAMPLES.md](references/EXAMPLES.md) | Need a JSON template for a style not in PROFILE_LIBRARY.md |
| [PUMP_AND_TRANSITIONS.md](references/PUMP_AND_TRANSITIONS.md) | User asks about adaptive flow, ease-in-out transitions, or power mode |
| [STOP_CONDITIONS.md](references/STOP_CONDITIONS.md) | User asks about combining multiple stop conditions or non-volumetric targets |
| [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) | User reports a problem with an **existing** profile — never for new creation |
| [FLOW_VARIABLE_PRESSURE.md](references/FLOW_VARIABLE_PRESSURE.md) | User specifically asks about Automatic Pro technique or flow-based variable pressure |
| [PROFILE_STRUCTURE.md](references/PROFILE_STRUCTURE.md) | Almost never — GAGGIMATE_PROFILE_CREATION_GUIDE.md covers the same fields |

### Step 4: Generate Profile JSON

Always output complete, valid JSON with ALL required fields:

```json
{
  "label": "Profile Name",
  "type": "pro",
  "description": "Optional description",
  "temperature": 93,
  "phases": [
    {
      "name": "Phase Name",
      "phase": "preinfusion|brew|decline",
      "valve": 1,
      "duration": 25,
      "temperature": 0,
      "transition": { "type": "instant", "duration": 0, "adaptive": true },
      "pump": { "target": "pressure", "pressure": 9, "flow": 0 },
      "targets": [{ "type": "volumetric", "operator": "gte", "value": 36 }]
    }
  ]
}
```

**Volumetric target:** Always set to `dose × ratio` using the user's basket size. Library profiles in PROFILE_LIBRARY.md are sized for 22g — adjust if user's basket differs.

### Step 5: Explain the Profile

After generating JSON, explain:
- What each phase does and why
- How the profile addresses the user's flavor goals
- Any adjustments they might want to try

### Step 6: Upload to Device

After generating the profile, confirm with user then upload:

1. **Ask for confirmation**: "Profile ready. Shall I upload it to your machine?"
2. **Create or update** via `manage_profile` MCP tool (action: `create` for new, `update` for existing)
3. **Verify** the upload succeeded by checking the MCP response

Always add `[AI]` suffix to profile names created by the agent.

## Quick Profile Patterns

### Classic 9-Bar (Medium Roasts)
```
Pre-infusion (4s, flow 3 ml/s) → Ramp (4s to 9 bar) → Hold (25s at 9 bar) → Stop at weight
```

### Bloom Profile (Light Roasts)
```
Fill (5s, flow 2.5 ml/s) → Bloom (8s, pump off) → Ramp (5s to 9 bar) → Hold (20s) → Stop at weight
```

### Lever Simulation (Any Roast)
```
Pre-infusion (5s, flow 3 ml/s) → Peak (5s to 9 bar) → Linear decline (25s to 3 bar) → Stop at weight
```

### Dark Roast Low Pressure
```
Pre-infusion (4s, flow 2.5 ml/s) → Ramp (3s to 7 bar) → Hold (25s) → Taper (4s to 4 bar)
```

## Essential Pump Modes

```json
// Pressure mode - maintain specific pressure
{ "target": "pressure", "pressure": 9, "flow": 4 }

// Flow mode - maintain specific flow rate
{ "target": "flow", "pressure": 9, "flow": 2.5 }

// Adaptive flow - auto-adjust to puck resistance
{ "target": "flow", "pressure": 9, "flow": -1 }

// Power mode (for bloom - pump off)
{ "target": "power", "pressure": 0, "flow": 0 }
```

## Essential Transition Types

| Type | Use Case |
|------|----------|
| `instant` | Phase starts, step changes |
| `linear` | Standard pressure ramps |
| `ease-in` | Gentle pre-infusion to extraction |
| `ease-out` | Tapering at end of shot |
| `ease-in-out` | Complex profiles, most natural |

## Output Requirements

1. **Always output complete, valid JSON** that can be directly imported
2. **Include all required fields** - don't omit any phase properties
3. **Use sensible defaults** - valve: 1, adaptive: true for most cases
4. **Add a volumetric target** on the final extraction phase (if scale available)
5. **Explain your choices** after the JSON
6. **Upload to device** via MCP after user confirms

## Resources

- **Documentation**: https://docs.gaggimate.eu/
- **Discord Community**: https://discord.gg/APw7rgPGPf
- **Web Interface**: http://gaggimate.local/profiles
- **GitHub**: https://github.com/jniebuhr/gaggimate
