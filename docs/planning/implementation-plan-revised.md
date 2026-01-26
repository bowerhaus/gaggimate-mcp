# Gaggimate MCP Python Implementation Plan (Revised)

## Design Principles Applied

Following MCP Server Design Principles, this implementation focuses on:

1. **Higher-level functions** over API endpoint mapping
2. **Minimal tool count** to reduce context overhead
3. **Composite operations** that solve specific workflow challenges
4. **Clear, concise tool descriptions** that guide agent behavior
5. **Security-first** with input validation and safety limits
6. **Fail-safe patterns** with graceful error handling

---

## Revised Tool Design: From 8 Tools → 5 Tools

### ❌ Old Approach (Too Many Tools)
~~8 tools mapping individual API operations~~
- ~~list_profiles, get_profile, create_profile, update_profile~~
- ~~list_shot_history, get_shot, get_shot_rating, update_shot_rating~~

### ✅ New Approach (Higher-Level Functions)
**5 workflow-oriented tools** that solve specific user tasks:

---

## MCP Tools (Revised)

### 1. `manage_profile`
**Purpose:** Unified profile management (list, get, create, update)

**Description:**
```
Manage espresso brewing profiles on your Gaggimate machine. Use this to:
- List all available profiles
- Get details of a specific profile
- Create new profiles for different beans (automatically tagged as agent-created)
- Update profiles you've created (safety limits applied)

Agent-created profiles are prefixed with "Agent-" and versioned locally for history.
```

**Input Schema:**
```json
{
  "action": {
    "type": "string",
    "enum": ["list", "get", "create", "update"],
    "description": "Action to perform"
  },
  "profile_id": {
    "type": "string",
    "description": "Profile ID (required for 'get' and 'update')"
  },
  "profile_data": {
    "type": "object",
    "description": "Profile configuration (required for 'create' and 'update')",
    "properties": {
      "name": {"type": "string", "description": "Profile name (Agent- prefix added automatically)"},
      "description": {"type": "string"},
      "temperature": {"type": "number", "description": "°C (60-96, enforced)"},
      "phases": {
        "type": "array",
        "description": "Brewing phases",
        "items": {
          "type": "object",
          "properties": {
            "name": {"type": "string", "description": "Phase name (e.g., Preinfusion, Extraction)"},
            "phase": {"enum": ["preinfusion", "brew"]},
            "duration": {"type": "number", "description": "Seconds"},
            "temperature": {"type": "number", "description": "Phase temperature (optional)"},
            "pump": {
              "type": "object",
              "properties": {
                "target": {"enum": ["pressure", "flow"]},
                "pressure": {"type": "number", "description": "Bar (0-12, enforced)"},
                "flow": {"type": "number", "description": "ml/s"}
              }
            },
            "transition": {
              "type": "object",
              "properties": {
                "type": {"enum": ["linear", "ease-out", "ease-in", "instant"]},
                "duration": {"type": "number", "description": "Seconds"}
              }
            },
            "targets": {
              "type": "array",
              "description": "Stop conditions",
              "items": {
                "type": "object",
                "properties": {
                  "type": {"enum": ["pressure", "flow", "volumetric", "pumped"]},
                  "operator": {"enum": ["gte", "lte"]},
                  "value": {"type": "number"}
                }
              }
            }
          },
          "required": ["name", "phase", "duration"]
        }
      }
    },
    "required": ["name", "temperature", "phases"]
  }
}
```

**Output:**
- **list**: `{"profiles": [{"id": "...", "label": "...", "agent_created": bool}, ...]}`
- **get**: `{"profile": {...full_profile_data...}}`
- **create**: `{"profile": {...}, "version_file": "profiles/...", "message": "Created Agent-ProfileName"}`
- **update**: `{"profile": {...}, "version_file": "profiles/...", "message": "Updated Agent-ProfileName to v2"}`

**Implementation Notes:**
- Single tool handles all profile operations
- Reduces context overhead (1 tool vs 4 tools)
- Clear action parameter makes intent explicit
- Composite operation: validates → saves version → calls API → returns result

---

### 2. `analyze_shot`
**Purpose:** Get comprehensive shot analysis with history context

**Description:**
```
Analyze espresso shot performance with detailed metrics. Retrieves shot data including:
- Extraction metrics (time, temperature, pressure, flow)
- Phase-by-phase breakdown
- Quality indicators (channeling, resistance, timing)
- Existing rating/feedback if available

Use this to understand what happened during a shot and inform profile adjustments.
```

**Input Schema:**
```json
{
  "shot_id": {
    "type": "string",
    "description": "Shot ID to analyze (use list_recent_shots to find IDs)"
  },
  "include_context": {
    "type": "boolean",
    "default": true,
    "description": "Include recent shot history for comparison"
  }
}
```

**Output:**
```json
{
  "shot": {
    "metadata": {...},
    "summary": {
      "temperature": {...},
      "pressure": {...},
      "flow": {...},
      "extraction": {...}
    },
    "phases": [...],
    "rating": {...existing_rating_if_available...}
  },
  "context": {
    "recent_shots": [
      {"id": "...", "rating": 4, "notes": "...", "profile": "..."}
    ],
    "profile_used": {...}
  }
}
```

**Implementation Notes:**
- Composite operation: get shot + parse binary + transform + fetch rating + get recent history
- Higher-level than simple "get_shot" - provides context for decision-making
- Single call gets all information needed for feedback

---

### 3. `record_shot_feedback`
**Purpose:** Record or update shot rating and tasting notes

**Description:**
```
Record your feedback about an espresso shot. Updates the shot's rating and notes.
Can add new feedback or update existing entries. All fields are optional - only
provide what you want to update.

Fields:
- rating: 0-5 stars
- dose_in/dose_out: Coffee in/out (grams)
- grind_setting: Grinder setting used
- balance_taste: bitter, balanced, or sour
- bean_type: Coffee bean name
- notes: Free-form tasting notes

Agent can use this to record user feedback during interactive dialing sessions.
```

**Input Schema:**
```json
{
  "shot_id": {"type": "string", "description": "Shot ID to rate"},
  "rating": {"type": "integer", "minimum": 0, "maximum": 5, "description": "Star rating"},
  "dose_in": {"type": "number", "description": "Grams of coffee used"},
  "dose_out": {"type": "number", "description": "Grams of espresso extracted"},
  "grind_setting": {"type": "string", "description": "Grind size setting"},
  "balance_taste": {"enum": ["bitter", "balanced", "sour"], "description": "Taste profile"},
  "bean_type": {"type": "string", "description": "Coffee bean name/origin"},
  "notes": {"type": "string", "description": "Tasting notes and observations"}
}
```

**Output:**
```json
{
  "success": true,
  "shot_id": "000123",
  "updated_fields": ["rating", "notes", "balance_taste"],
  "previous_rating": 3,
  "new_rating": 4,
  "message": "Updated feedback for shot 000123"
}
```

**Implementation Notes:**
- Composite operation: fetch existing → merge fields → validate → save → confirm
- Handles both new and existing ratings gracefully
- Returns what changed for transparency

---

### 4. `list_recent_shots`
**Purpose:** List recent shots with optional filtering

**Description:**
```
List recent espresso shots with filtering options. Returns shot summaries including:
- Shot ID and timestamp
- Profile used
- Duration and final weight
- Rating (if available)

Use this to find shots for analysis or to see recent brewing history.
```

**Input Schema:**
```json
{
  "limit": {
    "type": "integer",
    "default": 10,
    "maximum": 50,
    "description": "Number of shots to return"
  },
  "filter": {
    "type": "object",
    "description": "Optional filters",
    "properties": {
      "profile_id": {"type": "string", "description": "Filter by profile"},
      "min_rating": {"type": "integer", "minimum": 0, "maximum": 5},
      "unrated_only": {"type": "boolean", "description": "Show only unrated shots"}
    }
  }
}
```

**Output:**
```json
{
  "shots": [
    {
      "id": "000123",
      "timestamp": "2025-01-25T14:30:00Z",
      "profile": {"id": "...", "name": "Agent-Amizade"},
      "duration_seconds": 28.5,
      "final_weight_grams": 36.2,
      "rating": 4,
      "has_notes": true
    }
  ],
  "total_count": 45,
  "returned_count": 10
}
```

**Implementation Notes:**
- Composite operation: fetch index → parse → filter → enrich with ratings → return
- Client-side filtering for simplicity (API doesn't support filtering)
- Higher-level than raw "list_shot_history" - adds filtering and rating info

---

### 5. `dial_in_assistant`
**Purpose:** Interactive bean dialing workflow orchestration

**Description:**
```
Orchestrates the bean dialing process. This is a stateful assistant that helps dial in
new coffee beans through an interactive workflow:

1. Create initial profile based on bean parameters
2. Track shot results and gather feedback
3. Suggest adjustments based on taste feedback
4. Update profile incrementally

Use this for guided bean dialing sessions. The tool maintains state between calls
and provides structured guidance.
```

**Input Schema:**
```json
{
  "action": {
    "type": "string",
    "enum": ["start_session", "record_shot", "suggest_adjustment", "apply_adjustment", "end_session"],
    "description": "Workflow step"
  },
  "session_data": {
    "type": "object",
    "description": "Session context",
    "properties": {
      "bean_name": {"type": "string"},
      "bean_info": {"type": "string", "description": "Bean characteristics from research"},
      "profile_id": {"type": "string", "description": "Current working profile"},
      "shot_id": {"type": "string", "description": "Latest shot ID"},
      "user_feedback": {"type": "string", "description": "User's taste feedback"},
      "iteration": {"type": "integer", "description": "Iteration number"}
    }
  }
}
```

**Output (varies by action):**

**start_session:**
```json
{
  "session_id": "uuid",
  "profile": {...created_profile...},
  "next_step": "Pull a shot using Agent-BeanName profile, then tell me how it tastes",
  "questions": [
    "How would you rate the shot (1-5 stars)?",
    "Was it bitter, balanced, or sour?",
    "Any specific flavors you noticed?"
  ]
}
```

**record_shot:**
```json
{
  "recorded": true,
  "shot_analysis": {...},
  "suggestion": "Based on bitterness, I recommend lowering temperature by 2°C",
  "confidence": "medium",
  "rationale": "High extraction with bitter taste indicates over-extraction"
}
```

**suggest_adjustment:**
```json
{
  "suggested_changes": {
    "temperature": {"from": 93, "to": 91, "reason": "Reduce bitterness"},
    "pressure": {"from": 9, "to": 8.5, "reason": "Gentler extraction"}
  },
  "expected_outcome": "More balanced, less bitter, chocolate notes",
  "should_apply": true
}
```

**apply_adjustment:**
```json
{
  "updated_profile": {...},
  "version": 2,
  "changes_applied": ["temperature: 93→91°C", "pressure: 9→8.5 bar"],
  "next_step": "Pull another shot with updated profile"
}
```

**end_session:**
```json
{
  "session_summary": {
    "shots_pulled": 4,
    "iterations": 3,
    "final_rating": 4.5,
    "final_profile": {...},
    "improvements": ["Reduced bitterness", "Better balance", "Consistent extraction"]
  },
  "saved_profile": "Agent-Amizade_v3"
}
```

**Implementation Notes:**
- **Most complex tool** - handles entire workflow
- Maintains session state in memory
- Provides structured guidance at each step
- Encapsulates domain knowledge about espresso dialing
- Reduces back-and-forth by suggesting next steps
- Combines multiple operations into cohesive workflow

---

## Tool Count Rationale

### Why 5 Tools Instead of 8?

**MCP Principle #5:** *"Design Higher-Level Functions"*
- Avoid one-tool-per-API-endpoint pattern
- Group related tasks into cohesive workflows
- Focus on skills that solve specific workflow challenges

**Benefits:**
1. **Reduced context overhead**: 5 tool descriptions vs 8 (37% reduction)
2. **Clearer intent**: Action parameter makes operations explicit
3. **Better abstractions**: Tools map to user tasks, not API calls
4. **Composite operations**: Single calls accomplish multi-step workflows
5. **Easier to maintain**: Less code duplication, centralized logic

---

## Architecture (Updated)

### Project Structure
```
gaggimate-mcp-python/
├── pyproject.toml
├── README.md
├── .env.example
├── profiles/                      # Local version history
│   └── .gitkeep
├── src/
│   └── gaggimate_mcp/
│       ├── __init__.py
│       ├── server.py              # MCP server + tool registration
│       ├── config.py              # Configuration with Pydantic
│       ├── tools/                 # Tool implementations
│       │   ├── __init__.py
│       │   ├── manage_profile.py  # Profile management
│       │   ├── analyze_shot.py    # Shot analysis
│       │   ├── record_feedback.py # Rating/feedback
│       │   ├── list_shots.py      # Shot history
│       │   └── dial_in.py         # Workflow orchestration
│       ├── api/                   # Gaggimate API clients
│       │   ├── __init__.py
│       │   ├── client.py          # Unified client with pooling
│       │   ├── websocket.py       # WebSocket operations
│       │   └── http.py            # HTTP operations
│       ├── parsers/               # Binary parsers
│       │   ├── __init__.py
│       │   ├── binary_index.py
│       │   └── binary_shot.py
│       ├── transformers/
│       │   ├── __init__.py
│       │   └── shot_transformer.py
│       ├── models/                # Pydantic models
│       │   ├── __init__.py
│       │   ├── profile.py
│       │   ├── shot.py
│       │   ├── rating.py
│       │   └── session.py         # Dialing session state
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── profile_history.py
│       │   └── session_store.py   # Session state management
│       └── utils/
│           ├── __init__.py
│           ├── validation.py      # Safety validators
│           ├── errors.py          # Structured error classes
│           └── logging.py         # Structured logging
└── tests/
    └── __init__.py
```

---

## Security & Safety (Following Principles #2 & #3)

### Input Validation (Pydantic)
```python
from pydantic import BaseModel, Field, field_validator

class ProfileData(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    temperature: float = Field(ge=60.0, le=96.0)
    phases: list[PhaseData] = Field(min_items=1, max_items=10)

    @field_validator('temperature')
    def validate_temperature(cls, v):
        if v > 96.0:
            raise ValueError(f"Temperature {v}°C exceeds safety limit (96°C)")
        return v

class PhaseData(BaseModel):
    name: str
    phase: Literal["preinfusion", "brew"]
    duration: float = Field(gt=0, le=120)
    pump: PumpSettings

class PumpSettings(BaseModel):
    target: Literal["pressure", "flow"]
    pressure: float = Field(ge=0.0, le=12.0)
    flow: float = Field(ge=0.0)

    @field_validator('pressure')
    def validate_pressure(cls, v):
        if v > 12.0:
            raise ValueError(f"Pressure {v} bar exceeds safety limit (12 bar)")
        return v
```

### Structured Errors
```python
from enum import Enum
from dataclasses import dataclass

class ErrorCode(Enum):
    # Client errors (4xx)
    INVALID_INPUT = "invalid_input"
    PROFILE_NOT_FOUND = "profile_not_found"
    UNAUTHORIZED = "unauthorized"
    SAFETY_LIMIT_EXCEEDED = "safety_limit_exceeded"

    # Server errors (5xx)
    API_ERROR = "api_error"
    PARSE_ERROR = "parse_error"
    TIMEOUT = "timeout"

    # External errors
    DEVICE_UNREACHABLE = "device_unreachable"
    WEBSOCKET_ERROR = "websocket_error"

@dataclass
class GaggimateError(Exception):
    code: ErrorCode
    message: str
    details: dict = None
    retryable: bool = False

    def to_dict(self):
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details or {},
                "retryable": self.retryable
            }
        }
```

### Rate Limiting & Circuit Breaker
```python
from circuitbreaker import circuit
import time

class GaggimateClient:
    def __init__(self):
        self._last_request = 0
        self._min_interval = 0.1  # 100ms between requests

    async def _rate_limit(self):
        """Simple rate limiting"""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_request = time.time()

    @circuit(failure_threshold=5, recovery_timeout=30)
    async def send_websocket_request(self, request):
        """Circuit breaker prevents cascading failures"""
        await self._rate_limit()
        return await self._ws_send(request)
```

---

## Configuration (Principle #6)

### Config with Pydantic Validation
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class GaggimateConfig(BaseSettings):
    # Connection settings
    gaggimate_host: str = "gaggimate.local"
    gaggimate_protocol: str = "ws"
    request_timeout: float = 5.0

    # Safety limits
    max_temperature: float = 96.0
    min_temperature: float = 60.0
    max_pressure: float = 12.0
    min_pressure: float = 0.0

    # Storage
    profiles_dir: Path = Path("./profiles")

    # Agent settings
    agent_prefix: str = "Agent-"

    # Observability
    log_level: str = "INFO"
    enable_metrics: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "GAGGIMATE_"

    @property
    def websocket_url(self) -> str:
        return f"{self.gaggimate_protocol}://{self.gaggimate_host}/ws"

    @property
    def http_base_url(self) -> str:
        protocol = "https" if self.gaggimate_protocol == "wss" else "http"
        return f"{protocol}://{self.gaggimate_host}"

    def validate_temperature(self, temp: float) -> float:
        return max(self.min_temperature, min(self.max_temperature, temp))

    def validate_pressure(self, pressure: float) -> float:
        return max(self.min_pressure, min(self.max_pressure, pressure))
```

---

## Observability (Principle #9)

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Usage in tools
await logger.ainfo(
    "profile_created",
    profile_id=profile.id,
    profile_name=profile.label,
    temperature=profile.temperature,
    phases_count=len(profile.phases),
    version=version_num
)

await logger.aerror(
    "websocket_timeout",
    request_type="req:profiles:save",
    timeout_seconds=config.request_timeout,
    host=config.gaggimate_host,
    retry_attempt=retry_count
)
```

### Health Checks
```python
async def health_check() -> dict:
    """Multi-component health monitoring"""
    health = {
        "status": "healthy",
        "components": {}
    }

    # Check WebSocket connectivity
    try:
        await client.ping()
        health["components"]["websocket"] = "healthy"
    except Exception as e:
        health["components"]["websocket"] = f"unhealthy: {e}"
        health["status"] = "degraded"

    # Check HTTP API
    try:
        await client.fetch_shot_history(limit=1)
        health["components"]["http"] = "healthy"
    except Exception as e:
        health["components"]["http"] = f"unhealthy: {e}"
        health["status"] = "degraded"

    # Check storage
    try:
        config.profiles_dir.exists()
        health["components"]["storage"] = "healthy"
    except Exception as e:
        health["components"]["storage"] = f"unhealthy: {e}"
        health["status"] = "degraded"

    return health
```

---

## Implementation Phases (Revised)

### Phase 1: Foundation (Days 1-2)
- [x] Project setup with UV
- [x] Pydantic models and config
- [x] Structured error classes
- [x] Logging setup
- [ ] Basic MCP server skeleton

### Phase 2: API Client (Days 3-4)
- [ ] WebSocket client with connection pooling
- [ ] HTTP client with retry logic
- [ ] Circuit breaker implementation
- [ ] Rate limiting
- [ ] Health checks

### Phase 3: Binary Parsers (Day 5)
- [ ] Port binaryIndex parser
- [ ] Port binaryShot parser
- [ ] Shot transformer

### Phase 4: Core Tools (Days 6-8)
- [ ] `manage_profile` tool
- [ ] `list_recent_shots` tool
- [ ] `analyze_shot` tool
- [ ] `record_shot_feedback` tool
- [ ] Profile version storage

### Phase 5: Advanced Tool (Days 9-10)
- [ ] `dial_in_assistant` tool
- [ ] Session state management
- [ ] Workflow orchestration logic

### Phase 6: Testing & Polish (Days 11-12)
- [ ] Test with real Gaggimate device
- [ ] Integration with Claude Code
- [ ] Documentation
- [ ] Error handling refinement

---

## Usage Example (Revised Workflow)

### Example 1: Simple Profile Creation
```
User: "Create a profile for Brazilian medium roast beans, 93°C, 9 bar"

Claude calls: manage_profile
{
  "action": "create",
  "profile_data": {
    "name": "Brazilian Medium",
    "description": "Medium roast, chocolatey",
    "temperature": 93,
    "phases": [
      {
        "name": "Preinfusion",
        "phase": "preinfusion",
        "duration": 8,
        "pump": {"target": "pressure", "pressure": 2, "flow": 0}
      },
      {
        "name": "Extraction",
        "phase": "brew",
        "duration": 30,
        "pump": {"target": "pressure", "pressure": 9, "flow": 0},
        "targets": [{"type": "volumetric", "operator": "gte", "value": 36}]
      }
    ]
  }
}

Response: "Created Agent-Brazilian Medium (v1) with 2 phases"
```

### Example 2: Interactive Dialing Session
```
User: "Help me dial in these new Ethiopian beans" [uploads photo]

Claude: *researches beans* "These are light roast Ethiopian Yirgacheffe. Let me start a dialing session."

Claude calls: dial_in_assistant
{
  "action": "start_session",
  "session_data": {
    "bean_name": "Ethiopian Yirgacheffe",
    "bean_info": "Light roast, floral notes, high acidity, recommended 92-94°C"
  }
}

Response: {
  "session_id": "...",
  "profile": {...created Agent-Ethiopian Yirgacheffe...},
  "next_step": "Pull a shot, then tell me how it tastes",
  "questions": ["Rating?", "Bitter/balanced/sour?", "Flavors?"]
}

--- User pulls shot ---

User: "Okay, pulled the shot. It was a bit sour, maybe 3 stars"

Claude calls: dial_in_assistant
{
  "action": "record_shot",
  "session_data": {
    "session_id": "...",
    "shot_id": "000456",
    "user_feedback": "sour, 3 stars"
  }
}

Response: {
  "recorded": true,
  "suggestion": "Sourness indicates under-extraction. Recommend increasing temperature to 94°C",
  "confidence": "high"
}

Claude: "Let me update the profile temperature to 94°C"

Claude calls: dial_in_assistant
{
  "action": "apply_adjustment",
  "session_data": {
    "session_id": "...",
    "adjustments": {"temperature": 94}
  }
}

Response: {
  "updated_profile": {...},
  "version": 2,
  "next_step": "Pull another shot"
}

--- Iterates until satisfied ---

User: "This one is perfect! 5 stars"

Claude calls: dial_in_assistant
{"action": "end_session", "session_data": {"session_id": "..."}}

Response: {
  "session_summary": {
    "shots_pulled": 3,
    "final_rating": 5,
    "improvements": ["Fixed sourness", "Better extraction"]
  }
}
```

---

## Next Steps

1. **Review this revised plan** - Does it align with MCP principles?
2. **Start Phase 1** - Set up project foundation
3. **Build incrementally** - One tool at a time, test with real device

Ready to start implementation?
