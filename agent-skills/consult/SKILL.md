---
name: consult
description: Answer espresso knowledge questions from the authoritative knowledge files.
Use when the user asks about; temperature, pressure, ratios, grind settings, freshness,
extraction theory, puck prep, channeling, baskets, decaf, blends, milk steaming, drink specs,
profiles, shot styles, or any espresso concept. Routes to the correct knowledge file
and answers from its content rather than from memory or training data.
---

# Espresso Knowledge Consult Skill

You are answering an espresso knowledge question by consulting the authoritative knowledge files in your context. Do NOT answer from memory or training data — find the answer in the knowledge files first, then respond from their content.

> Adapted from [gaggimate-barista](https://github.com/charleshall888/gaggimate-barista) by Charlie Hall.

## Why This Skill Exists

All knowledge files are already loaded in your context. This skill ensures you **cite the correct file** rather than answering from general training data. The knowledge files contain Gaggimate-specific advice, tested parameters, and opinionated guidance that may differ from generic espresso advice.

## Workflow

### 1. CLASSIFY — Map Question to Knowledge File

Use the routing table below to identify which file(s) to consult. Match on keywords in the user's question.

| Keywords | Primary File | Secondary File |
|----------|-------------|----------------|
| temperature, temp, roast level, how hot | ESPRESSO_BREWING_BASICS.md | — |
| pressure, bar, processing method | PRESSURE_GUIDE.md | — |
| ratio, yield, dose, output, how much | ESPRESSO_BREWING_BASICS.md | — |
| grind, finer, coarser, grind setting | ESPRESSO_BREWING_BASICS.md | EXTRACTION_SCIENCE.md |
| sour, bitter, taste, flavor, tasting | ESPRESSO_TASTING_GUIDE.md | ESPRESSO_BREWING_BASICS.md |
| channeling, puck prep, WDT, distribution | EXTRACTION_SCIENCE.md | — |
| freshness, rest, degas, storage, freeze | BEAN_FRESHNESS_AND_STORAGE.md | — |
| profile, bloom, turbo, lever, allonge | PROFILE_LIBRARY.md | PRESSURE_GUIDE.md |
| decaf, blend, decaffeinated | SPECIAL_CATEGORIES.md | — |
| milk, steam, drink, cortado, cappuccino, latte, flat white | MILK_AND_DRINKS.md | — |
| basket, dose rule, headroom, puck depth | BASKETS.md | — |
| adjust, dial in, what to change, improvement | ESPRESSO_BREWING_BASICS.md | — |
| extraction, TDS, particle, solubility | EXTRACTION_SCIENCE.md | — |

If the question spans two topics (e.g., "what pressure for a natural at light roast?"), consult both the primary and secondary files.

If no keywords match, default to ESPRESSO_BREWING_BASICS.md — it covers the broadest range of topics.

### 2. ANSWER from File Content

Answer the user's question using the content from the identified knowledge file(s). **Cite specific tables, thresholds, or sections** from the file. Do not paraphrase from memory — use the actual data.

**Good:** "The pressure matrix in PRESSURE_GUIDE.md recommends 7-8 bar for light roast naturals."
**Bad:** "Light roast naturals generally do well at lower pressure." (no file reference, no specific value)

### 3. CROSS-REFERENCE (if needed)

If the answer touches multiple topics, check the cross-references at the bottom of each knowledge file. These point to related files that may have additional relevant information.

**Stop rule:** Consult at most **2 knowledge files** per question. If the primary file answers it, stop there.

---

## Quick Reference

**User asks:** "What temperature for a light roast?"
**Action:** Consult ESPRESSO_BREWING_BASICS.md → cite Temperature Guidelines table → answer "94-96°C"

**User asks:** "What pressure for an anaerobic natural?"
**Action:** Consult PRESSURE_GUIDE.md → cite Comprehensive Pressure Matrix → answer with specific bar range

**User asks:** "How do I store beans long-term?"
**Action:** Consult BEAN_FRESHNESS_AND_STORAGE.md → answer from storage section

**User asks:** "What basket should I use for 18g?"
**Action:** Consult BASKETS.md → cite dose rules → answer with basket recommendation

**User asks:** "My shot tastes sour AND bitter"
**Action:** Consult ESPRESSO_TASTING_GUIDE.md + ESPRESSO_BREWING_BASICS.md → cite channeling rule → recommend puck prep fix
