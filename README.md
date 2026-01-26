# Gaggimate MCP Server (Python)

Python MCP server for interactive espresso bean dialing with Gaggimate machines.

## Status: Phase 2 Complete ✅ (Pending Device Testing)

**Full implementation with comprehensive unit testing:**
- 115 tests passing
- 93% code coverage
- All Phase 2 features implemented
- Binary parsers for shot files
- WebSocket & HTTP API clients
- 5 fully functional MCP tools (including diagnostics)
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

#### Quick Start

**Option A: Using the wrapper script (easiest)**

1. **Get this repository's path:**
   ```bash
   cd /path/to/gaggimate-mcp
   pwd
   ```

2. **Open Claude Desktop settings:**
   - Go to **Settings → Developer → Edit Config**

3. **Add the configuration:**
   ```json
   {
     "mcpServers": {
       "gaggimate": {
         "command": "/path/to/gaggimate-mcp/run-mcp.sh"
       }
     }
   }
   ```
   Replace `/path/to/gaggimate-mcp` with the output from step 1.

4. **Save and restart Claude Desktop** (Cmd+Q to quit, then reopen)

**Option B: Direct uv command (recommended)**

1. **Find your `uv` absolute path:**
   ```bash
   which uv
   ```
   
   **⚠️ CRITICAL:** You must use the **full absolute path**, not just `uv`. Claude Desktop doesn't have access to your shell's PATH.
   
   Common locations:
   - `/Users/yourname/.pyenv/shims/uv` (pyenv)
   - `/Users/yourname/.local/bin/uv` (curl installer)
   - `/Users/yourname/.cargo/bin/uv` (cargo)
   - `/opt/homebrew/bin/uv` (Homebrew on Apple Silicon)
   - `/usr/local/bin/uv` (Homebrew on Intel Mac)

2. **Get this repository's absolute path:**
   ```bash
   pwd
   ```
   (Run from the gaggimate-mcp directory)

3. **Open Claude Desktop settings:**
   - Go to **Settings → Developer → Edit Config**

4. **Add the configuration:**
   ```json
   {
     "mcpServers": {
       "gaggimate": {
         "command": "/absolute/path/to/uv",
         "args": [
           "--directory",
           "/absolute/path/to/gaggimate-mcp",
           "run",
           "mcp",
           "run",
           "src/gaggimate_mcp/server.py"
         ]
       }
     }
   }
   ```

   **⚠️ Replace both placeholders with your actual paths:**
   - `/absolute/path/to/uv` → Output from `which uv` (step 1)
   - `/absolute/path/to/gaggimate-mcp` → Output from `pwd` (step 2)

   **Example (pyenv on macOS):**
   ```json
   {
     "mcpServers": {
       "gaggimate": {
         "command": "/Users/yourname/.pyenv/shims/uv",
         "args": [
           "--directory",
           "/Users/yourname/code/gaggimate-mcp",
           "run",
           "mcp",
           "run",
           "src/gaggimate_mcp/server.py"
         ]
       }
     }
   }
   ```

   **Example (Homebrew on macOS):**
   ```json
   {
     "mcpServers": {
       "gaggimate": {
         "command": "/opt/homebrew/bin/uv",
         "args": [
           "--directory",
           "/Users/yourname/code/gaggimate-mcp",
           "run",
           "mcp",
           "run",
           "src/gaggimate_mcp/server.py"
         ]
       }
     }
   }
   ```

5. **Save and restart Claude Desktop** (Cmd+Q to fully quit, then reopen)

#### Why Absolute Paths Are Required

Claude Desktop spawns MCP servers as separate processes **without your shell environment**. This means:
- It doesn't load `.bashrc`, `.zshrc`, or any shell profile
- PATH modifications from tools like pyenv, nvm, rbenv aren't available
- Commands like `uv` won't be found unless you specify the full path

If you see `Failed to spawn process: No such file or directory` in the MCP logs, this is almost always because the `uv` path isn't absolute.

#### Verification

Once Claude Desktop restarts:
- The Gaggimate server will appear in your MCP servers list
- **Network requirement:** You must be on the same network as your Gaggimate device
- The server connects to `gaggimate.local` by default (configurable in `.env`)

**Available tools:**
- 🔧 `manage_profile` - List/get/create/update espresso profiles
- 📊 `analyze_shot` - Analyze shot data with AI-friendly format
- 📝 `manage_shot_notes` - Manage shot ratings and tasting notes (synced to device)
- 📋 `list_recent_shots` - List shot history with ratings
- 🔍 `diagnose_connection` - Troubleshoot connectivity issues

#### Troubleshooting

**"Failed to spawn process: No such file or directory"**
This is the most common error. It means Claude Desktop can't find `uv`:
- ❌ **Wrong:** `"command": "uv"` or `"command": "/path/to/uv"`
- ✅ **Right:** `"command": "/Users/yourname/.pyenv/shims/uv"` (use output from `which uv`)

**Server won't start:**
- ✅ Make sure `uv` path is the **full absolute path** (run `which uv` to find it)
- ✅ Verify all paths don't have typos
- ✅ Use `mcp run` not `mcp dev` in the config
- ✅ Check logs in **Settings → Developer → MCP Logs**

**Connection errors:**
- ✅ Ensure you're on the same WiFi network as your Gaggimate
- ✅ Test connectivity: `ping gaggimate.local`
- ✅ Check `.env` file has correct `GAGGIMATE_HOST`
- ✅ If `gaggimate.local` doesn't resolve, find your device's IP in your router and use that instead
- ✅ Use the `diagnose_connection` tool to get automated troubleshooting guidance

**Browser access issues (ERR_CONNECTION_REFUSED):**

If your browser can't connect to `gaggimate.local` but ping works:

1. **Use HTTP explicitly:** Type `http://gaggimate.local` (not `https://`)
   - Browsers like Brave/Chrome often auto-upgrade to HTTPS, which the GaggiMate doesn't support
   - The "connection refused" error usually means the browser tried HTTPS on port 443

2. **Clear HSTS cache** (if HTTP still doesn't work):
   ```
   - Chrome/Brave: Go to chrome://net-internals/#hsts or brave://net-internals/#hsts
   - Under "Delete domain security policies", enter: gaggimate.local
   - Click Delete
   ```

3. **Use IP address directly:** Find the device IP and use `http://192.168.x.x`
   ```bash
   # Get the IP address
   ping gaggimate.local
   # Then use: http://192.168.178.117 (example)
   ```

4. **Bookmark the HTTP URL** to avoid auto-HTTPS issues in the future

**Can't find device:**
```bash
# Test if device is reachable
ping gaggimate.local

# Check if HTTP port is accessible
nc -zv gaggimate.local 80

# Use the diagnostic tool via Claude
# Ask Claude: "diagnose my Gaggimate connection"

# If ping fails, find device by IP via your router's admin page
```

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
- ✅ **`manage_shot_notes`** - Manage shot ratings/notes (synced to device)
  - Actions: `get`, `get_device`, `update`
  - Syncs to Gaggimate device via WebSocket API
  - Also stores locally as backup
  - Supports rating (0-5), notes, balance_taste, grind_setting, dose_in/out
  - Pydantic validation
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
