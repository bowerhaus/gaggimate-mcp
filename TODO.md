# TODO List

This file tracks pending tasks for the gaggimate-mcp project.

---

## Pending

- [ ] **Test MCP resources on real device** - Verify `gaggimate://knowledge`, `gaggimate://coffees`, `gaggimate://user/setup`, and `gaggimate://user/grind-map` resources work correctly in Claude Desktop
- [ ] **Test new write tools on real device** - Verify `manage_coffee`, `manage_user_setup`, and `manage_grind_map` tools create/update files correctly during actual dialing sessions
- [ ] **Re-zip agent skills** - Skills were updated to reference MCP resources; need to regenerate ZIP files for Claude Desktop upload
- [ ] **Fix pre-existing test_diagnostics failures** - 2 mDNS-related tests fail when device is not on network; consider mocking or skipping

---

## Completed

- [x] **MCP Resources implementation** - 6 read-only resources for knowledge files, coffee tracking, user setup, and grind map _(Completed: 2026-02-19)_
- [x] **Local data write tools** - `manage_coffee`, `manage_user_setup`, `manage_grind_map` MCP tools with markdown storage _(Completed: 2026-02-19)_
- [x] **Directory restructure** - `agent-knowledge/` → `knowledge/`, new `coffees/` and `user/` directories _(Completed: 2026-02-19)_
- [x] **Update instructions & skills** - All agent instructions and 5 skills updated to reference MCP resources and tools _(Completed: 2026-02-19)_
- [x] **Update README.md** - Documented new tools, resources, directory structure, and changelog _(Completed: 2026-02-19)_
- [x] **Test `select` action in `manage_profile`** - The new profile selection feature was implemented and tested with real device. _(Completed: 2026-02-06)_

