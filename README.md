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

# Run MCP server
uv run mcp dev src/gaggimate_mcp/server.py
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
- ✅ **Server with 5 Tools** - FastMCP server with tool implementations
  - `manage_profile` - Manage brewing profiles (list, get, create, update)
  - `analyze_shot` - Get comprehensive shot analysis
  - `record_shot_feedback` - Record ratings and tasting notes
  - `list_recent_shots` - List recent shots with filtering
  - `dial_in_assistant` - Interactive bean dialing workflow

## Next Steps (Phase 2)

- [ ] Implement WebSocket client for Gaggimate API
- [ ] Implement HTTP client for shot history
- [ ] Binary parsers for .slog and index.bin files
- [ ] Complete tool implementations (5 MCP tools)
- [ ] Profile version storage
- [ ] Integration testing with real device

## Project Structure

```
gaggimate-mcp/
├── src/gaggimate_mcp/
│   ├── config.py           # ✅ Configuration
│   ├── errors.py           # ✅ Error handling
│   ├── logging_config.py   # ✅ Logging setup
│   ├── server.py           # ✅ MCP server with tools
│   ├── models/             # ✅ Pydantic models
│   │   ├── profile.py      # ✅ Profile data structures
│   │   ├── shot.py         # ✅ Shot data structures
│   │   └── rating.py       # ✅ Rating/feedback structures
│   ├── api/                # 🔨 API clients (Phase 2)
│   ├── parsers/            # 🔨 Binary parsers (Phase 2)
│   ├── tools/              # 🔨 Tool implementations (Phase 2)
│   └── storage/            # 🔨 Profile versioning (Phase 2)
├── tests/                  # ✅ 97 tests, 99% coverage
├── docs/                   # Documentation
│   ├── planning/           # Implementation planning docs
│   └── reference/          # Reference documentation
├── typescript-reference/   # Original TypeScript implementation
└── profiles/               # Local profile version storage
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

## Documentation

- [Implementation Plan (Revised)](docs/planning/implementation-plan-revised.md) - Detailed implementation plan following MCP principles
- [Implementation Questions](docs/planning/implementation-questions.md) - Requirements and design decisions
- [MCP Server Principles](docs/reference/mcp-server-principles.md) - Design principles for MCP servers
- [Repository Overview](docs/reference/repository-overview.md) - Overview of the TypeScript reference implementation

## TypeScript Reference

The original TypeScript implementation is available in [`typescript-reference/`](typescript-reference/). See the [TypeScript README](typescript-reference/README.md) for more information.

## Related

- Blog post: [Brew by AI](https://archestra.ai/blog/brew-by-ai)
- Original repository: [Matvey-Kuk/gaggimate-mcp](https://github.com/Matvey-Kuk/gaggimate-mcp)
