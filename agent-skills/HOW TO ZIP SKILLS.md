# How to Zip Skills for Claude Desktop

## Command

From the `agent-skills` folder, run:

```bash
cd /Users/julianleopold/code/gaggimate-mcp/agent-skills && zip -r ../gaggimate-profiles-skill.zip gaggimate-profiles/
```

This creates `gaggimate-profiles-skill.zip` in the project root with the correct structure:

```
gaggimate-profiles/
├── SKILL.md
└── references/
    ├── EXAMPLES.md
    ├── FLOW_VARIABLE_PRESSURE.md
    ├── PROFILE_STRUCTURE.md
    ├── PUMP_AND_TRANSITIONS.md
    ├── QUICK_REFERENCE.md
    ├── STOP_CONDITIONS.md
    └── TROUBLESHOOTING.md
```

## Output Location

`/Users/julianleopold/code/gaggimate-mcp/agent-skills/gaggimate-profiles-skill.zip`
