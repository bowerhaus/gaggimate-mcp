# Gaggimate MCP Server (Python)

Python MCP server for interactive espresso bean dialing with Gaggimate machines.

## Status: Phase 1 Complete ✅

**Foundation built with comprehensive testing:**
- 97 tests passing
- 99% code coverage
- All core models implemented
- Configuration & error handling ready
- Structured logging configured
- MCP server skeleton created

## Setup

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your Gaggimate device hostname

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=gaggimate_mcp --cov-report=html
```

## What's Implemented (Phase 1)

### Core Infrastructure
- ✅ **Configuration Management** - Environment-based config with safety limits (96°C, 12 bar)
- ✅ **Error Handling** - 9 structured error codes with JSON serialization
- ✅ **Logging** - Structlog with JSON output to stderr (MCP-compliant)

### Data Models (Pydantic)
- ✅ **Profile Models** - Complete brewing profile structure with validation
  - PumpSettings, TransitionSettings, TargetCondition, PhaseData
  - Profile with auto-detection of agent-created profiles
- ✅ **Shot Models** - Shot analysis and history structures
  - Metadata, statistics (temp/pressure/flow/extraction)
  - Phase data, list items for history
- ✅ **Rating Models** - Shot feedback and tasting notes
  - Balance/taste enum, rating (0-5 stars), dose tracking
  - Automatic ratio calculation

### MCP Server
- ✅ **Server Skeleton** - Basic MCP server with 5 tool definitions
  - `manage_profile`, `analyze_shot`, `record_shot_feedback`
  - `list_recent_shots`, `dial_in_assistant`

## Next Steps (Phase 2)

- [ ] Implement WebSocket client for Gaggimate API
- [ ] Implement HTTP client for shot history
- [ ] Binary parsers for .slog and index.bin files
- [ ] Tool implementations (5 MCP tools)
- [ ] Profile version storage
- [ ] Integration testing with real device

## Project Structure

```
gaggimate-mcp-python/
├── src/gaggimate_mcp/
│   ├── config.py           # ✅ Configuration
│   ├── errors.py           # ✅ Error handling
│   ├── logging_config.py   # ✅ Logging setup
│   ├── server.py           # ✅ MCP server skeleton
│   ├── models/             # ✅ Pydantic models
│   │   ├── profile.py      # ✅ Profile data structures
│   │   ├── shot.py         # ✅ Shot data structures
│   │   └── rating.py       # ✅ Rating/feedback structures
│   ├── api/                # 🔨 API clients (Phase 2)
│   ├── parsers/            # 🔨 Binary parsers (Phase 2)
│   ├── tools/              # 🔨 Tool implementations (Phase 2)
│   └── storage/            # 🔨 Profile versioning (Phase 2)
└── tests/                  # ✅ 97 tests, 99% coverage
```

## Test Coverage

```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
src/gaggimate_mcp/config.py             26      0   100%
src/gaggimate_mcp/errors.py             25      1    96%
src/gaggimate_mcp/logging_config.py     10      0   100%
src/gaggimate_mcp/models/profile.py     42      0   100%
src/gaggimate_mcp/models/shot.py        60      0   100%
src/gaggimate_mcp/models/rating.py      31      0   100%
--------------------------------------------------------
TOTAL                                  194      1    99%
```

## Development

```bash
# Run all tests
uv run pytest -v

# Run with coverage report
uv run pytest --cov=gaggimate_mcp --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_config.py -v
```
