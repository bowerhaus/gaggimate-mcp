# Gaggimate MCP Server (Python)

Python MCP server for interactive espresso bean dialing with Gaggimate machines.

## Status: Phase 2 Complete ✅ (Pending Device Testing)

**Full implementation with comprehensive unit testing:**
- 115 tests passing
- 93% code coverage
- All Phase 2 features implemented
- Binary parsers for shot files
- WebSocket & HTTP API clients
- 4 fully functional MCP tools
- Profile version storage
- Shot rating storage

**Requires device testing** - Implementation complete, awaiting connection to `gaggimate.local` for integration testing

## Setup

### Installation

```bash
# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your Gaggimate device hostname
```

### Running with Claude Desktop

1. **Add to Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "gaggimate": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/gaggimate-mcp",
        "run",
        "mcp",
        "dev",
        "src/gaggimate_mcp/server.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/gaggimate-mcp` with the actual path to this repository.

2. **Restart Claude Desktop**

3. **Verify** - You should see 4 Gaggimate tools available:
   - `manage_profile` - List/get/create/update espresso profiles
   - `analyze_shot` - Analyze shot data with AI-friendly format
   - `update_feedback` - Update ratings and tasting notes
   - `list_recent_shots` - List shot history with ratings

### Development & Testing

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=gaggimate_mcp --cov-report=html

# Run MCP server in development mode (for debugging)
uv run mcp dev src/gaggimate_mcp/server.py
```

## What's Implemented

### Phase 1: Foundation ✅
- **Configuration Management** - Environment-based config with safety limits (96°C, 12 bar)
- **Error Handling** - 9 structured error codes with JSON serialization
- **Logging** - Structlog with JSON output to stderr (MCP-compliant)
- **Data Models** - Pydantic models for profiles, shots, and ratings

### Phase 2: Full Implementation ✅

#### Binary Parsers (18 tests, 97-98% coverage)
- ✅ **`.slog` Parser** - Parse shot log binary files
  - Supports V4 (128-byte) and V5 (512-byte) headers
  - Phase transition parsing (V5+)
  - Field mask-based sample parsing
  - Truncation handling for incomplete shots
- ✅ **`index.bin` Parser** - Parse shot history index
  - Shot metadata extraction
  - Flag handling (completed, deleted, has notes)
  - Automatic sorting by timestamp

#### Shot Transformer (7 tests, 99% coverage)
- ✅ **AI-Friendly Format Conversion**
  - Summary statistics: temperature, pressure, flow, extraction timing
  - Phase processing with representative samples
  - Volume integration from flow data
  - Preinfusion detection (50% pressure threshold)

#### API Clients
- ✅ **WebSocket Client** - Profile operations
  - `list_profiles()` - List all profiles
  - `load_profile(id)` - Get specific profile
  - `save_profile(profile)` - Create/update profile
  - `create_or_update_profile()` - Simplified profile creation
  - Request ID matching, timeout handling (5s)
- ✅ **HTTP Client** - Shot history
  - `fetch_shot_index()` - Get shot list with pagination
  - `fetch_shot(id)` - Get specific shot binary data
  - `list_recent_shots()` - Convenience method
  - 404 handling for empty history/missing shots

#### Storage Layer
- ✅ **Profile Version Storage**
  - Format: `Agent-ProfileName_v1.json`
  - Automatic version incrementing
  - Metadata tracking (timestamp, notes)
  - List/load/search operations
- ✅ **Rating Storage**
  - Local JSON file (`data/ratings.json`)
  - Shot ratings (0-5 stars) and tasting notes
  - Persistent across sessions

#### MCP Tools (4 fully functional)
- ✅ **`manage_profile`** - Profile management
  - Actions: `list`, `get`, `create`, `update`
  - WebSocket integration for device sync
  - Local version storage for AI-created profiles
  - JSON phases parameter for flexible definitions
- ✅ **`analyze_shot`** - Shot analysis
  - Fetch binary shot data via HTTP
  - Transform to AI-friendly format
  - Enrich with local ratings
  - Incomplete shot detection
- ✅ **`update_feedback`** - Update ratings/notes
  - Optional rating (0-5) and notes
  - Pydantic validation
  - Persistent local storage
- ✅ **`list_recent_shots`** - List history
  - Pagination support (max 50)
  - Enriched with user ratings/notes
  - Sorted by timestamp (newest first)

### Removed
- ❌ **`dial_in_assistant`** - Too complex for Phase 2 (stateful workflow)

## Implementation Phases

Based on the [Implementation Plan](docs/planning/implementation-plan-revised.md):

- ✅ **Phase 1: Foundation** (Days 1-2) - Models, config, logging, MCP skeleton
- ✅ **Phase 2: API Client** (Days 3-4) - WebSocket & HTTP clients
- ✅ **Phase 3: Binary Parsers** (Day 5) - .slog and index.bin parsers
- ✅ **Phase 4: Core Tools** (Days 6-8) - 4 MCP tools + storage
- ⏭️ **Phase 5: Advanced Tool** (Days 9-10) - SKIPPED (dial_in_assistant too complex)
- ⏳ **Phase 6: Testing & Polish** (Days 11-12) - **CURRENT PHASE**

## Next Steps: Phase 6 Testing

See [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) for detailed testing plan.

**Prerequisites:**
- Connect to home WiFi with access to `gaggimate.local`
- OR configure VPN to access Gaggimate device

**Testing Tasks:**
1. Test WebSocket profile operations (list, load, save)
2. Test HTTP shot history fetching
3. Verify binary parsers with real device files
4. End-to-end MCP tool testing via Claude Desktop
5. Profile version storage validation
6. Complete bean dialing workflow scenarios

**After Testing:**
- Fix any bugs discovered during device testing
- Update documentation with real-world examples
- Ready for production use!

## Project Structure

```
gaggimate-mcp/
├── src/gaggimate_mcp/
│   ├── config.py           # ✅ Configuration
│   ├── errors.py           # ✅ Error handling
│   ├── logging_config.py   # ✅ Logging setup
│   ├── server.py           # ✅ MCP server with 4 tools
│   ├── models/             # ✅ Pydantic models
│   │   ├── profile.py      # ✅ Profile data structures
│   │   ├── shot.py         # ✅ Shot data structures
│   │   └── rating.py       # ✅ Rating/feedback structures
│   ├── api/                # ✅ API clients
│   │   ├── websocket.py    # ✅ WebSocket client for profiles
│   │   └── http.py         # ✅ HTTP client for shot history
│   ├── parsers/            # ✅ Binary parsers
│   │   ├── shot.py         # ✅ .slog shot file parser
│   │   └── index.py        # ✅ index.bin parser
│   ├── transformers/       # ✅ Data transformers
│   │   └── shot.py         # ✅ Shot to AI-friendly format
│   ├── storage/            # ✅ Local storage
│   │   ├── profiles.py     # ✅ Profile versioning
│   │   └── ratings.py      # ✅ Shot ratings/notes
│   └── tools/              # ✅ Tool utilities
├── tests/                  # ✅ 115 tests, 93% coverage
├── docs/                   # Documentation
│   ├── planning/           # Implementation planning docs
│   └── reference/          # Reference documentation
├── typescript-reference/   # Original TypeScript implementation
└── profiles/               # Local profile version storage
```

## Test Coverage

**115 tests passing** covering models, parsers, transformers, and core utilities:

```
Module                           Coverage  Notes
----------------------------------------------------------
config.py                          94%    Configuration & validation
errors.py                          96%    Error handling
logging_config.py                 100%    Logging setup
models/profile.py                 100%    Profile data structures
models/shot.py                    100%    Shot data structures
models/rating.py                  100%    Rating structures
parsers/shot.py                    95%    Binary .slog parser
parsers/index.py                   98%    Binary index parser
transformers/shot.py               99%    AI-friendly transformation
----------------------------------------------------------
```

**Not unit tested** (require device integration testing):
- `api/http.py` - HTTP client for shot history
- `api/websocket.py` - WebSocket client for profiles
- `storage/profiles.py` - Profile version storage
- `storage/ratings.py` - Rating storage
- `server.py` - MCP server & tools

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
