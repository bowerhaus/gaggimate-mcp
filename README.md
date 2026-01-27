# Gaggimate MCP Server

> **Let AI help you dial in the perfect espresso shot** ☕

The Gaggimate MCP Server is a [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that gives AI agents the ability to interact with your [Gaggimate](https://github.com/jniebuhr/gaggimate)-powered espresso machine. MCP is an open standard that allows any compatible AI—Claude, GPT, Gemini, local models, or others—to connect to external tools and data sources through a standardized protocol.

This server exposes five high-level tools that handle the complexity of communicating with your espresso machine: reading and analyzing shot data, managing brewing profiles, and recording tasting feedback. Instead of manually navigating device menus or copying data, you can have a natural conversation with your AI assistant about your espresso workflow.

## Example Conversations

> "Here is a picture of this coffee I got. Can you please research it and create a Gaggimate profile for it?"

> "Can you please update the feedback for my most recent shot. It tasted a bit bitter. Give it a 2/5 rating. I used grind setting 12 with 15g in and 30g out."

> "Please look at all my recent shots with the Amizade coffee beans. Based on my feedback in each shot, how should we adjust the profile?"

## MCP Tools

This server provides five tools that give AI agents the capabilities they need to help with your espresso workflow:

### `manage_profile`
Create, view, update, and list brewing profiles on your Gaggimate device. Profiles define the entire extraction process—water temperature, pre-infusion settings, pressure curves, and flow targets. The AI can build profiles optimized for specific beans or brewing styles, and profiles created by AI are automatically tagged with `[AI]` in their name so you can identify them.

### `analyze_shot`
Retrieve comprehensive data from any shot, including temperature curves, pressure readings, flow rates, and extraction timing. The raw binary shot logs are parsed and transformed into an AI-friendly format with computed statistics like average pressure, temperature stability, and total extraction volume. This gives the AI the context it needs to understand what happened during extraction.

### `manage_shot_notes`
Record ratings (0-5 stars), tasting notes, and brewing parameters for any shot. Notes are synced directly to your Gaggimate device via WebSocket and also stored locally as backup. You can track taste balance (bitter/balanced/sour), grind settings, and dose weights. Notes added by AI are prefixed with `[llm agent]:` for transparency.

### `list_recent_shots`
Browse your shot history with optional filtering. Returns a list of recent shots with their IDs, timestamps, profile names, and any ratings you've recorded. This helps the AI understand your brewing patterns and find shots to analyze or compare.

### `diagnose_connection`
Troubleshoot connectivity issues between the MCP server and your Gaggimate device. Runs automated tests for network reachability, HTTP port access, API availability, and common misconfigurations. Returns specific recommendations if problems are detected.

## Requirements

- A [Gaggimate](https://github.com/jniebuhr/gaggimate)-modded espresso machine (Gaggia Classic, etc.)
- An MCP host application (e.g., [Claude Desktop](https://claude.ai/download), [VS Code with GitHub Copilot](https://code.visualstudio.com/), or any other MCP-compatible client)
- Python 3.11+ with [uv](https://docs.astral.sh/uv/) package manager
- Same network access as your Gaggimate device

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/julianleopold/gaggimate-mcp.git
cd gaggimate-mcp
uv sync
```

### 2. Configure Your MCP Client

Find your `uv` path (you'll need the full absolute path):
```bash
which uv
# Example output: /opt/homebrew/bin/uv
```

Get this repository's path:
```bash
pwd
# Example output: /Users/yourname/code/gaggimate-mcp
```

#### Claude Desktop

Open Claude Desktop settings: **Settings → Developer → Edit Config**

Add this configuration (replace paths with your actual values):

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

#### Other MCP Hosts

For other MCP hosts, configure the server using the stdio transport with the command:
```bash
uv --directory /path/to/gaggimate-mcp run mcp run src/gaggimate_mcp/server.py
```

### 3. Restart Your MCP Host

Restart your MCP host application to load the new server configuration. You should see the Gaggimate tools become available.

### 4. Start Chatting!

Make sure you're on the same network as your Gaggimate device, then try:
- "List my Gaggimate profiles"
- "Show my recent espresso shots"
- "Diagnose my Gaggimate connection" (if having issues)

## Configuration

By default, the server connects to `gaggimate.local`. To customize, create a `.env` file:

```bash
cp .env.example .env
```

Available settings:
```ini
GAGGIMATE_HOST=gaggimate.local    # Device hostname or IP
GAGGIMATE_PROTOCOL=ws             # Protocol (ws or http)
GAGGIMATE_LOG_LEVEL=INFO          # Logging level
```

If your device doesn't resolve via mDNS, use the IP address directly:
```ini
GAGGIMATE_HOST=192.168.1.100
```

## Troubleshooting

### "Failed to spawn process: No such file or directory"

This means your MCP host can't find `uv`. You must use the **full absolute path**:
- ❌ `"command": "uv"`
- ✅ `"command": "/opt/homebrew/bin/uv"`

Run `which uv` to find your correct path.

### Can't connect to Gaggimate

1. **Check network**: Are you on the same WiFi as your espresso machine?
   ```bash
   ping gaggimate.local
   ```

2. **Try IP address**: If mDNS doesn't work, find your device's IP in your router and update `.env`

3. **Use diagnostics**: Ask "diagnose my Gaggimate connection" for automated troubleshooting

### Browser shows "ERR_CONNECTION_REFUSED"

Browsers often auto-upgrade to HTTPS. Gaggimate uses HTTP:
- Use `http://gaggimate.local` explicitly (not https)
- Or use the IP address: `http://192.168.x.x`

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   MCP Client    │────▶│  Gaggimate MCP   │────▶│   Gaggimate     │
│  (Claude, etc.) │◀────│     Server       │◀────│   (ESP32)       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │                       │                        │
        │    MCP Protocol       │    WebSocket/HTTP      │
        │    (stdio)            │    (local network)     │
```

The MCP server acts as a bridge:
- **WebSocket API** (`ws://gaggimate.local/ws`) - Profile management, shot notes
- **HTTP API** (`http://gaggimate.local/api/`) - Shot history and data files

Shot data is parsed from binary `.slog` files and transformed into an AI-friendly format with statistics about temperature, pressure, flow, and extraction timing.

## Extended Examples

### Creating a Profile

> **You:** I have some light roast Ethiopian beans. Can you create a profile?
>
> **AI:** I'll create a profile optimized for light roast Ethiopian beans. Light roasts typically benefit from higher temperatures and longer pre-infusion...
>
> *Creates "Ethiopian Light [AI]" profile with appropriate settings*

### Analyzing a Shot

> **You:** Analyze my last shot, it tasted sour
>
> **AI:** Looking at shot #127... The extraction was 24 seconds with an average pressure of 8.2 bar. The flow rate increased rapidly after pre-infusion, which combined with the sour taste suggests under-extraction. I'd recommend:
> 1. Grinding finer
> 2. Increasing temperature by 1-2°C
> 3. Extending pre-infusion time

### Tracking Progress

> **You:** Rate that last shot 4 stars - much better, slight bitterness remaining
>
> **AI:** I've saved your rating and notes. Looking at your progression, your last 3 shots have improved from 2 to 4 stars. The bitterness might indicate we're now slightly over-extracting. Want me to adjust the profile?

## Development

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=gaggimate_mcp --cov-report=html

# Development mode (for debugging)
uv run mcp dev src/gaggimate_mcp/server.py
```

**Test Status:** 119 tests passing, 93% coverage

## Project Structure

```
gaggimate-mcp/
├── src/gaggimate_mcp/
│   ├── server.py           # MCP server with 5 tools
│   ├── config.py           # Configuration management
│   ├── api/                # Device communication
│   │   ├── websocket.py    # WebSocket client (profiles, notes)
│   │   └── http.py         # HTTP client (shot history)
│   ├── parsers/            # Binary file parsers
│   │   ├── shot.py         # .slog shot file parser
│   │   └── index.py        # index.bin parser
│   ├── models/             # Data models
│   └── storage/            # Local storage (ratings, profile versions)
├── tests/                  # Test suite
└── data/                   # Local data storage
    ├── ratings.json        # Your shot ratings
    └── profiles/           # AI-created profile versions
```

## Related

- [Gaggimate Project](https://github.com/jniebuhr/gaggimate) - The ESP32 mod for Gaggia machines
- [Brew by AI](https://archestra.ai/blog/brew-by-ai) - Blog post about AI-assisted espresso brewing
- [Original TypeScript Implementation](https://github.com/Matvey-Kuk/gaggimate-mcp) - Reference implementation

## License

MIT License - See [LICENSE](LICENSE) for details.

---

**Made with ☕ for the espresso-obsessed**
