# CLAUDE.md - Instructions writing code

## ⚠️ CRITICAL: Repository Scope Restriction

**This workspace is for `julianleopold/gaggimate-mcp` ONLY.**

### DO NOT interact with external repositories

**NEVER** perform any actions on these repositories:
- ❌ `Matvey-Kuk/gaggimate-mcp` - This is an EXTERNAL repository, NOT ours
- ❌ Any other `gaggimate-mcp` repository that is not `julianleopold/gaggimate-mcp`

### ALLOWED repositories:
- ✅ `julianleopold/gaggimate-mcp` - This is OUR repository


## Project Overview

This is a Python MCP (Model Context Protocol) server for Gaggimate espresso machine integration.

### Key directories:
- `src/gaggimate_mcp/` - Main source code
- `tests/` - Test files
- `data/` - JSON data files (ratings, profiles)
- `docs/` - Documentation

### Development commands:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv sync

# Run tests
pytest

# Run with coverage
pytest --cov=src/gaggimate_mcp
```
