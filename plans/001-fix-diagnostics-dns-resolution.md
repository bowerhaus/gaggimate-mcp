# Fix `check_port` DNS resolution in diagnostics

**GitHub issue:** [bowerhaus/gaggimate-mcp#1](https://github.com/bowerhaus/gaggimate-mcp/issues/1) (bug) — the PR for this branch should close it (e.g. "Closes #1"). Target repo for the PR is the fork `bowerhaus/gaggimate-mcp`, not upstream `julianleopold/gaggimate-mcp`.

## Context

`diagnose_connection` reported `port_closed` for a healthy GaggiMate ("HTTP port 80 not accessible: DNS resolution failed: " — note the empty error), yet the device's web server is reachable from a browser on port 80. The failure is entirely inside the diagnostic tool's `check_port` function ([src/gaggimate_mcp/diagnostics.py:110](src/gaggimate_mcp/diagnostics.py#L110)), not the device.

Two real bugs there:

1. **`AF_UNSPEC` resolution hangs on the IPv6 (AAAA) mDNS query, then the timeout is mislabeled as a DNS failure.** `check_port` resolves with `socket.getaddrinfo(host, port, AF_UNSPEC, ...)` wrapped in `asyncio.wait_for(timeout=2.0)`. For a `.local` host, `AF_UNSPEC` issues both A and AAAA mDNS queries. The `except (socket.gaierror, asyncio.TimeoutError)` at [line 131](src/gaggimate_mcp/diagnostics.py#L131) catches the `TimeoutError` and formats it as `f"DNS resolution failed: {str(e)}"` — but `str(asyncio.TimeoutError())` is `""`, producing the blank message. Meanwhile the `ping` test passed because it resolves via the faster IPv4-only `socket.gethostbyname` ([line 41](src/gaggimate_mcp/diagnostics.py#L41)).

   > **Verified via live testing (root cause correction):** the timeout is *not merely too short* — the IPv6 lookup hangs for the **entire** timeout regardless of its value. Measured for `gaggimate.local:80`: `getaddrinfo AF_INET` → **0.00s**; `getaddrinfo AF_INET6` → **5.00s** (full timeout); `getaddrinfo AF_UNSPEC` → **5.00s** (gated by the AAAA query). So bumping the timeout does **not** fix it — the correct fix is to resolve **IPv4-only (`AF_INET`)**, matching `ping_host`. GaggiMate is an IPv4-only ESP32. The 2s→5s bump is kept only as defensive headroom.

2. **Wrong `getaddrinfo` unpacking (latent).** [Lines 126-130](src/gaggimate_mcp/diagnostics.py#L126-L130) do `_, _, _, _, addr = await ... getaddrinfo(...)` then `ip = addr[0][0]`. `getaddrinfo` returns a *list* of 5-tuples, not a single 5-tuple. The unpack only works when the list happens to have exactly 5 entries; otherwise it raises `ValueError` (uncaught by the gaierror/timeout handler). It hasn't fired yet only because the timeout hit first.

## Approach

Rewrite the resolution block of `check_port` only. Connection logic below it stays as-is.

### `src/gaggimate_mcp/diagnostics.py`

- **Resolve IPv4-only (`AF_INET`)** — the primary fix. Matches `ping_host`'s `gethostbyname` and avoids the hanging IPv6 (AAAA) mDNS query that `AF_UNSPEC` waits on.
- Bump the `check_port` default `timeout` from `2.0` to `5.0` as defensive headroom (the sole caller, [line 262](src/gaggimate_mcp/diagnostics.py#L262), uses the default). With `AF_INET` resolution is near-instant, so the timeout is now a backstop, not the fix.
- Fix the unpack: `getaddrinfo` returns a list — take the first entry's sockaddr, e.g.
  ```python
  infos = await asyncio.wait_for(
      asyncio.to_thread(socket.getaddrinfo, host, port, socket.AF_INET, socket.SOCK_STREAM),
      timeout=timeout,
  )
  ip = infos[0][4][0]   # first result's sockaddr, first element is the address
  ```
- Split the combined `except` into two so a timeout is no longer mislabeled and never blank:
  ```python
  except asyncio.TimeoutError:
      return {"open": False, "error": f"DNS resolution timed out after {timeout}s (mDNS/.local can be slow)"}
  except socket.gaierror as e:
      return {"open": False, "error": f"DNS resolution failed: {e}"}
  ```
- Guard the empty-result edge case: if `getaddrinfo` returns `[]`, return a clear `"No addresses found for {host}"` rather than `IndexError`.

No change to `ping_host`, `check_http_endpoint`, `diagnose_connection`, or config.

### `tests/test_diagnostics.py`

Existing tests mock `check_port` wholesale, so they keep passing. Add focused `check_port` unit tests (patching `socket.getaddrinfo` and `asyncio.open_connection`):
- success: multi-entry `getaddrinfo` list → `open: True` (proves the unpack fix);
- `asyncio.TimeoutError` from resolution → `open: False` and a non-empty error containing "timed out";
- `socket.gaierror` → `open: False` and "DNS resolution failed".

## Verification — DONE

- `PYTHONPATH=src uv run pytest tests/test_diagnostics.py` — **9 passed** (incl. new `check_port` cases).
- Live check against the real device (direct `uv run python -c` invoking `check_port`/`diagnose_connection`): `check_port(80)` → `{open: True}`, `overall_status: healthy`.
- MCP server restarted (`pkill -f "mcp run src/gaggimate_mcp/server.py"`, then re-invoked the tool to respawn with new code) — `diagnose_connection` MCP tool now returns `status: healthy`.

## Notes

- Per CLAUDE.md: this touches `src/`, not `agent-skills/` or `agent-instructions/`, so no skill version stamping is required. It's a user-facing bug fix — add a dated entry to the README Changelog (newest at top).
