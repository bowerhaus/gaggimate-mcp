# Phase 6 Testing Checklist

**Status:** Phase 2-5 complete, awaiting device access for integration testing

## Prerequisites

Before starting testing:
1. ✅ Ensure you're connected to home WiFi or VPN with access to `gaggimate.local`
2. ✅ Verify Gaggimate device is powered on and connected to network
3. ✅ Test basic connectivity: `ping gaggimate.local`
4. ✅ Configure Claude Desktop with MCP server (see below)

## Components Status

### ✅ Already Tested (Unit Tests - 115 passing, 93% coverage)
- [x] Binary parser for .slog files (5 tests)
- [x] Binary parser for index.bin files (6 tests)
- [x] Shot transformer (7 tests)
- [x] All Pydantic models (65+ tests)
- [x] Configuration & error handling (29 tests)

### ⚙️ Implemented (Needs Device Testing)
- [x] WebSocket client implementation
- [x] HTTP client implementation
- [x] Profile version storage
- [x] Rating storage
- [x] All 4 MCP tools

---

## Testing Plan

### 🔄 Step 1: Basic Connectivity Tests

**Goal:** Verify network connectivity and API accessibility

```bash
# Test network
ping gaggimate.local

# Test HTTP endpoint
curl http://gaggimate.local/api/history/index.bin -I

# Test WebSocket (if wscat installed)
# wscat -c ws://gaggimate.local/ws
```

**Expected:**
- ✅ Ping succeeds
- ✅ HTTP returns 200 or 404 (not connection refused)
- ✅ WebSocket connects successfully

---

### 🔄 Step 2: Configure Claude Desktop

Add to your Claude Desktop MCP configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "gaggimate": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/julianleopold/code/gaggimate-mcp",
        "run",
        "mcp",
        "dev",
        "src/gaggimate_mcp/server.py"
      ],
      "env": {
        "GAGGIMATE_HOST": "gaggimate.local",
        "GAGGIMATE_PROTOCOL": "ws",
        "GAGGIMATE_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Test:**
- [ ] Restart Claude Desktop
- [ ] Verify MCP server appears in Claude Desktop
- [ ] Check that 4 tools are available (manage_profile, analyze_shot, record_shot_feedback, list_recent_shots)

---

### 🔄 Step 3: WebSocket Client Tests

Test via Claude Desktop or Python REPL:

#### Test 1: List Profiles
```python
# Ask Claude: "List all my Gaggimate profiles"
# Or in Python:
from gaggimate_mcp.api.websocket import GaggimateWebSocketClient
import asyncio

client = GaggimateWebSocketClient()
profiles = asyncio.run(client.list_profiles())
print(f"Found {len(profiles)} profiles")
```

**Expected:** List of all profiles from device

- [ ] WebSocket connects successfully
- [ ] Request sent with correct format
- [ ] Response received with profiles array
- [ ] No connection errors or timeouts

#### Test 2: Load Specific Profile
```python
# Ask Claude: "Show me the details of profile X"
# Or use profile ID from list above
```

**Expected:** Full profile details with phases

- [ ] Profile loaded successfully
- [ ] All phase data present
- [ ] Temperature/pressure values correct

#### Test 3: Create Profile
```python
# Ask Claude: "Create a test profile at 92°C with 9 bar pressure"
```

**Expected:** Profile created on device and version saved locally

- [ ] Profile created on device
- [ ] Profile appears in device profile list
- [ ] Local version file created: `data/profiles/TestProfile [AI]_v1.json`
- [ ] Version metadata recorded

---

### 🔄 Step 4: HTTP Client Tests

#### Test 1: Fetch Shot Index
```python
# Ask Claude: "Show me my recent shots"
# Or in Python:
from gaggimate_mcp.api.http import GaggimateHTTPClient
import asyncio

client = GaggimateHTTPClient()
shots = asyncio.run(client.fetch_shot_index(limit=5))
print(f"Found {len(shots)} shots")
for shot in shots:
    print(f"  Shot {shot['id']}: {shot['profile']} @ {shot['timestamp']}")
```

**Expected:** List of recent shots with metadata

- [ ] HTTP request succeeds
- [ ] Binary index.bin parsed correctly
- [ ] Shots sorted by timestamp (newest first)
- [ ] Profile names decoded correctly from C strings

#### Test 2: Fetch Specific Shot
```python
# Ask Claude: "Analyze shot 000123" (use real shot ID from above)
# Or in Python:
shot_data = asyncio.run(client.fetch_shot("1"))  # Use actual shot ID
print(f"Shot samples: {shot_data.sample_count}")
print(f"Profile: {shot_data.profile_name}")
```

**Expected:** Complete shot data with samples

- [ ] HTTP request succeeds
- [ ] Binary .slog file parsed correctly
- [ ] All samples decoded
- [ ] Phase transitions parsed (if V5 format)
- [ ] Temperature/pressure/flow values reasonable

#### Test 3: Handle Missing Shot
```python
shot = asyncio.run(client.fetch_shot("999999"))
assert shot is None  # Should handle 404 gracefully
```

**Expected:** Returns None, no exception

- [ ] 404 handled gracefully (returns None)
- [ ] No exception thrown

---

### 🔄 Step 5: Shot Transformer Tests

```python
# After fetching a real shot (Step 4):
from gaggimate_mcp.transformers.shot import transform_shot_for_ai

transformed = transform_shot_for_ai(shot_data)

print("Summary:")
print(f"  Temp: {transformed['summary']['temperature']}")
print(f"  Pressure: {transformed['summary']['pressure']}")
print(f"  Flow: {transformed['summary']['flow']}")
print(f"  Extraction: {transformed['summary']['extraction']}")
print(f"Phases: {len(transformed['phases'])}")
```

**Expected:** AI-friendly format with statistics

- [ ] Summary statistics calculated correctly
- [ ] Temperature min/max/avg make sense
- [ ] Pressure peak time detected
- [ ] Flow volume integrated correctly
- [ ] Preinfusion time detected (50% pressure threshold)
- [ ] Phases processed with representative samples

---

### 🔄 Step 6: MCP Tools End-to-End Tests

Test all 4 tools via Claude Desktop conversation:

#### Test 1: `list_recent_shots`
**Claude prompt:** "Show me my 5 most recent espresso shots"

**Expected:**
- [ ] Tool called successfully
- [ ] Returns list of shots with metadata
- [ ] Shots sorted by timestamp
- [ ] Any user ratings/notes included
- [ ] JSON response parsed correctly

#### Test 2: `analyze_shot`
**Claude prompt:** "Analyze shot 1 in detail" (use real shot ID)

**Expected:**
- [ ] Shot fetched from device
- [ ] Binary data parsed correctly
- [ ] Transformed to AI-friendly format
- [ ] Summary statistics present
- [ ] Phase data included (if available)
- [ ] User rating enriched (if exists)

#### Test 3: `record_shot_feedback`
**Claude prompt:** "Rate shot 1 as 4 stars with note 'slightly bitter'"

**Expected:**
- [ ] Rating saved to `data/ratings.json`
- [ ] File created if doesn't exist
- [ ] Timestamp recorded
- [ ] Subsequent `analyze_shot` includes this rating

#### Test 4: `manage_profile` - List
**Claude prompt:** "List all my Gaggimate brewing profiles"

**Expected:**
- [ ] All profiles returned from device
- [ ] Profile names, IDs, temperatures visible
- [ ] Response includes count

#### Test 5: `manage_profile` - Get
**Claude prompt:** "Show me the full details of profile X"

**Expected:**
- [ ] Profile details fetched
- [ ] All phases included
- [ ] Temperature, pressure, transitions visible

#### Test 6: `manage_profile` - Create
**Claude prompt:** "Create a profile called 'TestBean' at 92°C with a 5-second preinfusion at 3 bar followed by 25 seconds extraction at 9 bar"

**Expected:**
- [ ] Profile created on device
- [ ] Local version saved: `data/profiles/Agent-TestBean_v1.json`
- [ ] Version file has metadata (timestamp, phase count)
- [ ] Profile appears in device profile list
- [ ] Profile prefixed with "Agent-"

#### Test 7: `manage_profile` - Update
**Claude prompt:** "Update the TestBean profile to use 93°C instead"

**Expected:**
- [ ] Profile updated on device
- [ ] New version saved: `data/profiles/Agent-TestBean_v2.json`
- [ ] Temperature changed correctly
- [ ] Can still load v1 for comparison

---

### 🔄 Step 7: Storage Tests

#### Profile Version Storage
```bash
# Check profile versions created
ls -la data/profiles/

# Verify JSON format
cat data/profiles/Agent-TestBean_v1.json
```

**Expected:**
- [ ] Files created with correct naming: `Agent-Name_v1.json`
- [ ] JSON contains: version, profile_name, timestamp, profile, metadata
- [ ] Can list versions via Python:
  ```python
  from gaggimate_mcp.storage.profiles import ProfileStorage
  storage = ProfileStorage()
  versions = storage.list_profile_versions("TestBean")
  print(versions)
  ```

#### Rating Storage
```bash
# Check ratings file
cat data/ratings.json
```

**Expected:**
- [ ] File created at `data/ratings.json`
- [ ] JSON object mapping shot_id to rating data
- [ ] Each rating has: shot_id, rating, notes, timestamp

---

### 🔄 Step 8: Complete Bean Dialing Workflow

**Goal:** Test the full workflow from bean research to profile iteration

1. **Research** (Claude prompt): "I have Ethiopian Yirgacheffe beans. What's a good starting profile?"
   - [ ] Claude provides recommendations

2. **Create Profile** (Claude prompt): "Create a profile for these beans at 93°C with gentle preinfusion"
   - [ ] Profile created successfully

3. **Pull Shot** (Manual): Use Gaggimate to pull a shot with the new profile

4. **Analyze** (Claude prompt): "Analyze my most recent shot"
   - [ ] Shot data fetched and analyzed
   - [ ] Statistics presented

5. **Record Feedback** (Claude prompt): "Rate that shot 3 stars - it was under-extracted and sour"
   - [ ] Feedback saved

6. **Iterate** (Claude prompt): "Adjust the profile to increase extraction - maybe higher temp or longer time"
   - [ ] Claude suggests adjustments
   - [ ] Profile updated
   - [ ] New version saved

---

## Known Limitations

Document any issues discovered during testing:

1. **Network Requirements**
   - Cannot test without access to `gaggimate.local`
   - Requires home WiFi or VPN

2. **Binary Format**
   - Must match firmware version exactly
   - May need updates if firmware changes

3. **WebSocket Protocol**
   - Request ID matching required
   - 5-second timeout (may need adjustment)

4. **Safety**
   - Profile changes affect real machine
   - Test with non-critical profiles first
   - Don't test extreme temperatures/pressures

5. **Firmware Compatibility**
   - Implementation based on TypeScript reference
   - May have discrepancies with actual firmware
   - Document any API differences found

---

## Bugs Found During Testing

Use this section to track issues:

| # | Issue | Severity | Status | Notes |
|---|-------|----------|--------|-------|
| | | | | |

---

## Testing Completion Checklist

- [ ] All connectivity tests passed
- [ ] WebSocket client works with real device
- [ ] HTTP client fetches real files correctly
- [ ] Binary parsers handle real data
- [ ] Shot transformer produces valid statistics
- [ ] All 4 MCP tools functional in Claude Desktop
- [ ] Profile version storage working
- [ ] Rating storage working
- [ ] Complete workflow tested end-to-end
- [ ] No critical bugs found (or all bugs documented/fixed)
- [ ] Ready for production use
