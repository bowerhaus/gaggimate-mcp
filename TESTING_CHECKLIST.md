# Testing Checklist for Phase 2

## Components to Test with Real Device

### ✅ Already Tested (Unit Tests)
- [x] Binary parser for .slog files
- [x] Binary parser for index.bin files

### 🔄 Needs Device Testing

#### WebSocket Client
- [ ] Connect to `ws://gaggimate.local/ws`
- [ ] List profiles (`req:profiles:list`)
- [ ] Load specific profile (`req:profiles:load`)
- [ ] Save/update profile (`req:profiles:save`)
- [ ] Handle connection errors/timeouts
- [ ] Verify request/response matching by `rid`

#### HTTP Client
- [ ] Fetch `http://gaggimate.local/api/history/index.bin`
- [ ] Fetch `http://gaggimate.local/api/history/XXXXXX.slog` (specific shot)
- [ ] Handle 404 for missing shots
- [ ] Handle connection errors/timeouts
- [ ] Verify binary data parsing with real files

#### Shot Transformer
- [ ] Transform real shot data to AI-friendly format
- [ ] Verify statistics calculations (min/max/avg)
- [ ] Verify phase detection works with real data

#### MCP Tools (End-to-End)
- [ ] `manage_profile` - list all profiles
- [ ] `manage_profile` - get specific profile
- [ ] `manage_profile` - create new profile
- [ ] `manage_profile` - update existing profile
- [ ] `analyze_shot` - get detailed shot analysis
- [ ] `record_shot_feedback` - save rating/notes locally
- [ ] `list_recent_shots` - list shot history

#### Profile Version Storage
- [ ] Create profile versions on disk
- [ ] List profile versions
- [ ] Verify file naming (Agent-ProfileName_v1.json)

## Test Scenarios

### Scenario 1: Profile Management
```
1. List all profiles from device
2. Get a specific profile by ID
3. Create new profile "Agent-TestBean"
4. Verify it appears on device
5. Update the profile temperature
6. Verify changes on device
```

### Scenario 2: Shot Analysis
```
1. List recent shots
2. Get most recent shot details
3. Verify temperature/pressure/flow data parses correctly
4. Transform shot for AI analysis
5. Save feedback (rating, notes)
```

### Scenario 3: Bean Dialing Workflow
```
1. Research bean parameters (web search)
2. Create initial profile for bean
3. User pulls shot
4. Analyze shot data
5. Record user feedback
6. Iterate profile adjustments
```

## Known Limitations (Document These)
- Cannot test without VPN/home network access to `gaggimate.local`
- Binary format must exactly match firmware version
- WebSocket protocol requires request ID matching
- Profile changes affect real machine - be careful!

## Testing Strategy
1. **Mock Testing First** - Write tests with mock data before device access
2. **Incremental Device Testing** - Test one component at a time
3. **Safety First** - Don't create profiles that could damage machine
4. **Document Failures** - Note any API discrepancies vs TypeScript implementation
