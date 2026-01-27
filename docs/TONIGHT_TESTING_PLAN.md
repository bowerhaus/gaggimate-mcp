# Tonight's Testing Plan - Quick Start

**Status:** Phase 2-5 complete. Ready for Phase 6 device testing.

## Quick Start (5 minutes)

1. **Connect to home WiFi/VPN** - Ensure you can reach `gaggimate.local`

2. **Test basic connectivity:**
   ```bash
   ping gaggimate.local
   curl http://gaggimate.local/api/history/index.bin -I
   ```

3. **Configure Claude Desktop** - Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
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
           "GAGGIMATE_PROTOCOL": "ws"
         }
       }
     }
   }
   ```

4. **Restart Claude Desktop**

5. **Test in Claude Desktop:**
   - "List all my Gaggimate profiles"
   - "Show me my 5 most recent espresso shots"
   - "Analyze shot 1" (use real shot ID)
   - "Rate shot 1 as 4 stars with note 'smooth but slightly bitter'"

## What's Been Built (115 tests passing, 93% coverage)

✅ **Binary Parsers**
- `.slog` shot file parser (V4 & V5)
- `index.bin` history index parser
- Full sample data extraction

✅ **API Clients**
- WebSocket client for profile operations
- HTTP client for shot history
- Proper error handling & timeouts

✅ **Shot Transformer**
- AI-friendly format conversion
- Summary statistics (temp, pressure, flow, extraction)
- Phase processing

✅ **Storage**
- Profile version storage (`data/profiles/Agent-Name_v1.json`)
- Rating storage (`data/ratings.json`)

✅ **4 MCP Tools**
- `manage_profile` (list, get, create, update)
- `analyze_shot` (detailed analysis)
- `record_shot_feedback` (ratings & notes)
- `list_recent_shots` (with rating enrichment)

## Testing Priorities

### Critical (Must Work)
1. List profiles from device
2. List recent shots from device
3. Analyze a real shot

### Important (Should Work)
4. Create a test profile
5. Record shot feedback
6. Profile version storage

### Nice to Have
7. Update profile
8. Complete bean dialing workflow

## Common Issues to Watch For

1. **Network connectivity** - Most common issue
   - Solution: Check WiFi/VPN, ping gaggimate.local

2. **Binary format mismatch** - If firmware version differs
   - Document any parsing errors
   - Check sample counts, field masks

3. **WebSocket timeout** - If 5 seconds too short
   - Can adjust in config

4. **Claude Desktop MCP not loading**
   - Check logs: `~/Library/Logs/Claude/mcp*.log`
   - Verify uv path in config

## Full Testing Checklist

See [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) for comprehensive step-by-step guide with:
- 8 testing sections
- Expected outputs for each test
- Code examples
- Bug tracking table

## After Testing

1. **Document any bugs** in TESTING_CHECKLIST.md bugs table
2. **Note any API differences** from TypeScript reference
3. **Fix critical bugs** if any found
4. **Celebrate!** 🎉 Phase 2-6 complete!

## Next Phases (Optional Future Work)

After successful testing, potential enhancements:

- **Phase 7: Advanced Features** (Optional)
  - `dial_in_assistant` stateful workflow
  - Session state management
  - Multi-shot comparison

- **Phase 8: Polish** (Optional)
  - Connection pooling
  - Circuit breaker pattern
  - Rate limiting
  - Health checks
  - Metrics/telemetry

- **Phase 9: Production** (Optional)
  - Deployment guide
  - Error monitoring
  - Performance optimization
  - Additional safety checks
