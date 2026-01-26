# Gaggimate MCP Python Implementation Plan

## Summary of Requirements

Based on your answers and API research, here's what we're building:

### Use Case
**Interactive bean dialing workflow:**
1. Upload photo of coffee beans to Claude
2. Claude researches bean parameters via web search
3. Claude creates initial profile via MCP → Gaggimate
4. You brew a shot
5. Claude asks specific questions about taste
6. Claude updates shot rating/notes via MCP → Gaggimate
7. Claude iteratively adjusts profile based on feedback

### Key Features
- ✅ Create new profiles (with "Agent-" suffix for tracking)
- ✅ Edit only agent-created profiles
- ✅ Add/edit shot ratings and feedback (all fields)
- ✅ List profiles and shots
- ✅ Get detailed shot and profile data
- ✅ Local profile version history
- ✅ Safety limits (max temp: 96°C, max pressure: 12 bar)
- ✅ Manual profile deletion only (no agent deletion)

---

## API Capabilities (Research Findings)

### ✅ Shot Rating/Feedback - FULLY SUPPORTED
**WebSocket Messages:**
- `req:history:notes:get` - Get existing notes for a shot
- `req:history:notes:save` - Create/update shot notes

**Available Fields:**
- `rating` (0-5 stars)
- `doseIn` (grams)
- `doseOut` (grams)
- `ratio` (calculated automatically)
- `grindSetting` (text)
- `balanceTaste` ("bitter", "balanced", "sour")
- `notes` (free text)
- `beanType` (appears to be stored in notes field based on UI)

**Storage:** `/h/{shotId}.json` on device

### ✅ Profile Creation - FULLY SUPPORTED
**WebSocket Messages:**
- `req:profiles:save` - Creates new profile OR updates existing one
- `req:profiles:delete` - Deletes profile (manual only in our implementation)

**Profile Structure:**
```json
{
  "id": "uuid-or-empty-for-new",
  "label": "Agent-ProfileName",
  "type": "pro",
  "description": "Created by AI agent for [bean name]",
  "temperature": 93,
  "favorite": false,
  "selected": false,
  "phases": [...]
}
```

---

## Python MCP Server Architecture

### Technology Stack
```
Python 3.11+
├── uv (package manager)
├── mcp (official Python MCP SDK)
├── websockets (WebSocket client)
├── aiohttp (async HTTP client)
├── pydantic (data validation)
└── pathlib (profile versioning storage)
```

### Project Structure
```
gaggimate-mcp-python/
├── pyproject.toml                 # UV project config
├── README.md                      # Setup instructions
├── .gitignore
├── profiles/                      # Local profile version history
│   └── .gitkeep
├── src/
│   └── gaggimate_mcp/
│       ├── __init__.py
│       ├── server.py              # MCP server setup
│       ├── config.py              # Configuration
│       ├── tools/                 # MCP tool implementations
│       │   ├── __init__.py
│       │   ├── profiles.py        # Profile tools
│       │   ├── shots.py           # Shot history tools
│       │   └── ratings.py         # Rating/feedback tools
│       ├── api/                   # Gaggimate API clients
│       │   ├── __init__.py
│       │   ├── websocket.py       # WebSocket client
│       │   └── http.py            # HTTP client
│       ├── parsers/               # Binary data parsers
│       │   ├── __init__.py
│       │   ├── binary_index.py    # Parse index.bin
│       │   └── binary_shot.py     # Parse .slog files
│       ├── transformers/          # Data transformers
│       │   ├── __init__.py
│       │   └── shot_transformer.py
│       ├── models/                # Pydantic data models
│       │   ├── __init__.py
│       │   ├── profile.py
│       │   ├── shot.py
│       │   └── rating.py
│       └── storage/               # Profile version history
│           ├── __init__.py
│           └── profile_history.py
└── tests/
    └── __init__.py
```

---

## MCP Tools Implementation

### 1. Profile Management Tools

#### `list_profiles`
**Description:** List all brewing profiles from Gaggimate device
**Input:** None
**Output:** Array of profiles with metadata (id, label, type, agent-created flag)
**Implementation:** WebSocket `req:profiles:list`

#### `get_profile`
**Description:** Get detailed profile configuration
**Input:** `profile_id` (string)
**Output:** Complete profile JSON
**Implementation:** WebSocket `req:profiles:load`

#### `create_profile`
**Description:** Create a new brewing profile (automatically adds "Agent-" prefix)
**Input:**
- `name` (string) - Base name (e.g., "Amizade Medium Roast")
- `description` (string) - Profile description
- `temperature` (float) - Target temp (60-96°C, enforced)
- `phases` (array) - Brewing phases
  - `name` (string)
  - `phase` ("preinfusion" | "brew")
  - `duration` (float) - seconds
  - `temperature` (float) - phase temp (optional)
  - `pump` (object)
    - `target` ("pressure" | "flow")
    - `pressure` (float) - bars (0-12, enforced)
    - `flow` (float) - ml/s
  - `transition` (object)
    - `type` ("linear" | "ease-out" | "ease-in" | "instant")
    - `duration` (float) - seconds
  - `targets` (array) - stop conditions (optional)
    - `type` ("pressure" | "flow" | "volumetric" | "pumped")
    - `operator` ("gte" | "lte")
    - `value` (float)

**Output:** Created profile with ID
**Safety:**
- Temperature clamped to max 96°C
- Pressure clamped to max 12 bar
- Auto-prefixes label with "Agent-"
- Saves version to local `profiles/` directory

**Implementation:**
1. Validate parameters (enforce limits)
2. Generate profile JSON with "Agent-" prefix
3. Send WebSocket `req:profiles:save` (without ID for new profile)
4. Save version to `profiles/{timestamp}_{sanitized_name}.json`
5. Return created profile

#### `update_profile`
**Description:** Update an existing agent-created profile
**Input:** Same as `create_profile` + `profile_id`
**Output:** Updated profile
**Safety:**
- Only allows updating profiles with "Agent-" prefix
- Creates new version in local storage
- Enforces same limits as create

**Implementation:**
1. Fetch existing profile with `get_profile`
2. Verify label starts with "Agent-" (reject otherwise)
3. Update fields with new values
4. Send WebSocket `req:profiles:save` (with existing ID)
5. Save new version to `profiles/{timestamp}_{sanitized_name}.json`

### 2. Shot History Tools

#### `list_shot_history`
**Description:** List brewing history with pagination
**Input:**
- `limit` (int, optional) - Max shots to return
- `offset` (int, optional) - Skip first N shots

**Output:** Array of shot summaries
**Implementation:** HTTP GET `/api/history/index.bin` → parse binary

#### `get_shot`
**Description:** Get detailed shot data with analysis
**Input:** `shot_id` (string)
**Output:** Complete shot data (metadata, summary stats, phases)
**Implementation:** HTTP GET `/api/history/{shotId}.slog` → parse binary → transform

### 3. Rating/Feedback Tools

#### `get_shot_rating`
**Description:** Get existing rating/notes for a shot
**Input:** `shot_id` (string)
**Output:** Rating object (or null if unrated)
**Implementation:** WebSocket `req:history:notes:get`

#### `update_shot_rating`
**Description:** Add or update shot rating and feedback
**Input:**
- `shot_id` (string)
- `rating` (int, 0-5) - Star rating (optional)
- `dose_in` (float) - Grams of coffee (optional)
- `dose_out` (float) - Grams of espresso (optional)
- `grind_setting` (string) - Grind size (optional)
- `balance_taste` ("bitter" | "balanced" | "sour") - Taste profile (optional)
- `bean_type` (string) - Bean name (optional, stored in notes)
- `notes` (string) - Free-form notes (optional)

**Output:** Updated rating object
**Implementation:**
1. Fetch existing notes with `req:history:notes:get`
2. Merge new fields with existing data
3. Send WebSocket `req:history:notes:save`

**Note:** Can update existing ratings (including user-created ones)

---

## Local Storage: Profile Version History

### Storage Location
`profiles/` directory in project root

### Filename Format
`{timestamp}_{profile_name}_v{version}.json`

Example: `20250125_143022_Agent-Amizade_v1.json`

### Version Tracking
- Each profile create/update saves a new version
- Versions are sequential per profile name
- Metadata includes:
  - `created_at` (ISO timestamp)
  - `profile_id` (Gaggimate UUID)
  - `version` (integer)
  - `agent_created` (boolean, always true)
  - `profile_data` (full profile JSON)

### Storage Implementation
```python
# src/gaggimate_mcp/storage/profile_history.py

from pathlib import Path
from datetime import datetime
import json

PROFILES_DIR = Path(__file__).parent.parent.parent.parent / "profiles"

def save_profile_version(profile: dict) -> Path:
    """Save profile version to local storage"""
    PROFILES_DIR.mkdir(exist_ok=True)

    # Extract name and sanitize
    name = profile["label"].replace("Agent-", "")
    sanitized = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_"))
    sanitized = sanitized.replace(" ", "_")

    # Find next version number
    existing = list(PROFILES_DIR.glob(f"*_{sanitized}_v*.json"))
    version = len(existing) + 1

    # Create filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{sanitized}_v{version}.json"
    filepath = PROFILES_DIR / filename

    # Save with metadata
    data = {
        "created_at": datetime.now().isoformat(),
        "profile_id": profile.get("id"),
        "version": version,
        "agent_created": True,
        "profile_data": profile
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    return filepath
```

---

## Safety Features

### 1. Temperature Limits
```python
def clamp_temperature(temp: float) -> float:
    """Clamp temperature to safe range (60-96°C)"""
    return max(60.0, min(96.0, temp))
```

### 2. Pressure Limits
```python
def clamp_pressure(pressure: float) -> float:
    """Clamp pressure to safe range (0-12 bar)"""
    return max(0.0, min(12.0, pressure))
```

### 3. Agent-Created Profile Detection
```python
def is_agent_profile(profile: dict) -> bool:
    """Check if profile was created by agent"""
    return profile.get("label", "").startswith("Agent-")
```

### 4. Profile Edit Authorization
```python
def can_edit_profile(profile: dict) -> bool:
    """Check if agent can edit this profile"""
    if not is_agent_profile(profile):
        raise PermissionError(
            f"Cannot edit profile '{profile['label']}'. "
            "Agent can only edit profiles it created (with 'Agent-' prefix)."
        )
    return True
```

---

## Configuration

### Environment Variables
```bash
GAGGIMATE_HOST=gaggimate.local  # Device hostname
GAGGIMATE_PROTOCOL=ws           # WebSocket protocol (ws or wss)
PROFILES_DIR=./profiles         # Local profile storage (optional)
```

### Config File (`src/gaggimate_mcp/config.py`)
```python
import os
from pathlib import Path

class Config:
    GAGGIMATE_HOST = os.getenv("GAGGIMATE_HOST", "gaggimate.local")
    GAGGIMATE_PROTOCOL = os.getenv("GAGGIMATE_PROTOCOL", "ws")
    HTTP_PROTOCOL = "https" if GAGGIMATE_PROTOCOL == "wss" else "http"

    WEBSOCKET_URL = f"{GAGGIMATE_PROTOCOL}://{GAGGIMATE_HOST}/ws"
    HTTP_BASE_URL = f"{HTTP_PROTOCOL}://{GAGGIMATE_HOST}"

    REQUEST_TIMEOUT = 5.0  # seconds

    PROFILES_DIR = Path(os.getenv("PROFILES_DIR", "./profiles"))

    # Safety limits
    MAX_TEMPERATURE = 96.0  # °C
    MIN_TEMPERATURE = 60.0  # °C
    MAX_PRESSURE = 12.0     # bar
    MIN_PRESSURE = 0.0      # bar

    # Agent profile prefix
    AGENT_PREFIX = "Agent-"
```

---

## Development Setup

### 1. Initialize Project
```bash
# Create project directory
mkdir gaggimate-mcp-python
cd gaggimate-mcp-python

# Initialize UV project
uv init
uv python pin 3.11

# Add dependencies
uv add mcp websockets aiohttp pydantic

# Create directory structure
mkdir -p src/gaggimate_mcp/{tools,api,parsers,transformers,models,storage}
mkdir -p profiles tests
touch src/gaggimate_mcp/__init__.py
# ... (create all __init__.py files)
```

### 2. Running the Server
```bash
# Activate environment
source .venv/bin/activate

# Set environment variables
export GAGGIMATE_HOST=gaggimate.local

# Run MCP server
uv run python -m gaggimate_mcp.server
```

### 3. Testing with Claude Code
Add to Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "gaggimate": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/julianleopold/code/gaggimate-mcp-python",
        "run",
        "python",
        "-m",
        "gaggimate_mcp.server"
      ],
      "env": {
        "GAGGIMATE_HOST": "gaggimate.local"
      }
    }
  }
}
```

---

## Deployment Options

### Option 1: Local Only (Easiest)
- Run MCP server locally on your machine
- Claude Code connects via stdio
- No deployment needed

### Option 2: Shared MCP Server (Future)
- Deploy Python MCP server to a cloud VM
- Multiple users connect to same instance
- Requires authentication & multi-device support
- **Out of scope for now** (use local setup first)

---

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Project setup with UV
- [ ] Basic MCP server skeleton
- [ ] WebSocket client (profiles only)
- [ ] HTTP client (shot history)
- [ ] Pydantic models for profiles and shots

### Phase 2: Profile Management
- [ ] `list_profiles` tool
- [ ] `get_profile` tool
- [ ] `create_profile` tool (with safety limits)
- [ ] `update_profile` tool (with agent-only restriction)
- [ ] Local profile version storage

### Phase 3: Shot History
- [ ] Binary parser for `index.bin`
- [ ] Binary parser for `.slog` files
- [ ] Shot transformer (AI-friendly format)
- [ ] `list_shot_history` tool
- [ ] `get_shot` tool

### Phase 4: Rating/Feedback
- [ ] `get_shot_rating` tool
- [ ] `update_shot_rating` tool
- [ ] WebSocket shot notes API integration

### Phase 5: Testing & Documentation
- [ ] Test with real Gaggimate device
- [ ] Document MCP tool usage
- [ ] Create example workflows
- [ ] README with setup instructions

---

## Example Workflow

### Dialing in New Beans

**Step 1: User uploads bean photo to Claude**
```
User: [uploads photo of Amizade coffee bag]
"Help me dial in these new beans"
```

**Step 2: Claude researches parameters**
```
Claude: *uses web search*
"These are Amizade beans, medium roast from Brazil.
Recommended parameters:
- Temperature: 93°C
- Pressure: 9 bar
- Ratio: 1:2
- Time: 25-30 seconds

Let me create a profile for you."
```

**Step 3: Claude creates profile via MCP**
```python
# Claude calls: create_profile
{
  "name": "Amizade Medium Roast",
  "description": "Brazilian medium roast, chocolatey notes",
  "temperature": 93,
  "phases": [
    {
      "name": "Preinfusion",
      "phase": "preinfusion",
      "duration": 8,
      "pump": {"target": "pressure", "pressure": 2, "flow": 0},
      "transition": {"type": "linear", "duration": 2}
    },
    {
      "name": "Extraction",
      "phase": "brew",
      "duration": 30,
      "pump": {"target": "pressure", "pressure": 9, "flow": 0},
      "targets": [{"type": "volumetric", "operator": "gte", "value": 30}]
    }
  ]
}
```

**Step 4: User brews shot**
```
User: "Just pulled a shot, it was okay but a bit bitter"
```

**Step 5: Claude asks follow-up questions**
```
Claude: "Let me help you refine this. A few questions:

1. On a scale of 1-5 stars, how would you rate this shot?
2. How much coffee did you use (dose in)?
3. How much came out (dose out)?
4. What's your grind setting?
5. Would you describe the taste as: bitter, balanced, or sour?
6. Any specific notes about the flavor?"
```

**Step 6: Claude updates shot rating via MCP**
```python
# User responds, Claude calls: update_shot_rating
{
  "shot_id": "000123",
  "rating": 3,
  "dose_in": 18,
  "dose_out": 36,
  "grind_setting": "15",
  "balance_taste": "bitter",
  "bean_type": "Amizade",
  "notes": "Slightly bitter, dark chocolate notes but not balanced yet. Need to adjust."
}
```

**Step 7: Claude adjusts profile**
```
Claude: "Based on the bitterness, let's try:
- Lower temperature to 91°C
- Reduce pressure slightly to 8.5 bar
- Aim for faster extraction

Updating the profile now..."

# Claude calls: update_profile (with same profile_id)
```

**Step 8: Iterate**
User brews another shot, Claude continues refining until optimal.

---

## Next Steps

1. **API Exploration**: Test WebSocket and HTTP endpoints with your local Gaggimate device
2. **Start Implementation**: Begin with Phase 1 (core infrastructure)
3. **Iterate**: Build tools incrementally, test with Claude Code as you go

Would you like me to start implementing Phase 1?
