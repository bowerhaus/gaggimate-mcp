"""MCP server for Gaggimate espresso machine."""

#!/usr/bin/env python3

import json
import asyncio
from typing import Optional
from pydantic import ValidationError

from mcp.server.fastmcp import FastMCP
from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.logging_config import setup_logging, get_logger
from gaggimate_mcp.api.websocket import GaggimateWebSocketClient
from gaggimate_mcp.api.http import GaggimateHTTPClient
from gaggimate_mcp.transformers.shot import transform_shot_for_ai
from gaggimate_mcp.storage.profiles import ProfileStorage
from gaggimate_mcp.storage.ratings import RatingStorage
from gaggimate_mcp.models.rating import ShotRating, BalanceTaste
from gaggimate_mcp.errors import GaggimateError
from gaggimate_mcp.diagnostics import diagnose_connection as run_diagnostics


# Initialize configuration and logging
config = GaggimateConfig()
setup_logging(log_level=config.log_level)
logger = get_logger(__name__)

# Create FastMCP server
mcp = FastMCP("gaggimate-mcp")

# Initialize clients and storage
ws_client = GaggimateWebSocketClient(config)
http_client = GaggimateHTTPClient(config)
profile_storage = ProfileStorage(config)
rating_storage = RatingStorage(config)


def _get_error_suggestion(error: GaggimateError) -> str:
    """Generate user-friendly error suggestion based on error code.

    Args:
        error: GaggimateError instance

    Returns:
        Helpful suggestion for resolving the error
    """
    from gaggimate_mcp.errors import ErrorCode

    suggestions = {
        ErrorCode.DEVICE_UNREACHABLE: (
            f"Cannot reach Gaggimate device at {config.host}. "
            "Please check: 1) Device is powered on, 2) Connected to same network, "
            "3) Correct IP address/hostname is configured. "
            "Run 'diagnose_connection' tool for detailed diagnostics."
        ),
        ErrorCode.WEBSOCKET_ERROR: (
            f"WebSocket connection failed to {config.host}. "
            "Please verify: 1) Device is online, 2) WebSocket port is accessible, "
            "3) No firewall blocking connection. "
            "Run 'diagnose_connection' tool for detailed diagnostics."
        ),
        ErrorCode.TIMEOUT: (
            f"Request timed out waiting for response from {config.host}. "
            "Please check: 1) Device is responding (try accessing web UI), "
            "2) Network connection is stable, 3) Device is not overloaded. "
            "Run 'diagnose_connection' tool for detailed diagnostics."
        ),
        ErrorCode.API_ERROR: (
            "Gaggimate API returned an error. "
            "The request format may be invalid or the device rejected the operation. "
            "Check the error message for details."
        ),
        ErrorCode.PARSE_ERROR: (
            "Failed to parse response from Gaggimate. "
            "The device may be running incompatible firmware or the data format changed. "
            "Consider updating the MCP server or checking device firmware version."
        ),
        ErrorCode.PROFILE_NOT_FOUND: (
            "Profile not found on device. "
            "Use 'manage_profile' with action='list' to see available profiles."
        ),
        ErrorCode.SHOT_NOT_FOUND: (
            "Shot not found on device. "
            "Use 'list_recent_shots' to see available shot IDs. "
            "Note: Shot IDs are 6-digit numbers (e.g., '000100')."
        ),
    }

    return suggestions.get(error.code, "Please check the error message and try again.")


@mcp.tool()
async def manage_profile(
    action: str,
    profile_id: Optional[str] = None,
    profile_name: Optional[str] = None,
    temperature: Optional[float] = None,
    phases: Optional[str] = None
) -> str:
    """Manage espresso brewing profiles.

    Args:
        action: Action to perform (list, get, create, update)
        profile_id: Profile ID (required for 'get' and 'update')
        profile_name: Profile name (required for 'create' and 'update')
        temperature: Temperature in Celsius (required for 'create' and 'update')
        phases: JSON string of phases array (required for 'create' and 'update')

    Returns:
        JSON string with result
    """
    logger.info("manage_profile_called", action=action, profile_id=profile_id)

    try:
        if action == "list":
            profiles = await ws_client.list_profiles()
            return json.dumps({
                "success": True,
                "action": "list",
                "profiles": profiles,
                "count": len(profiles)
            })

        elif action == "get":
            if not profile_id:
                return json.dumps({
                    "success": False,
                    "error": "profile_id is required for 'get' action"
                })

            profile = await ws_client.load_profile(profile_id)
            if not profile:
                return json.dumps({
                    "success": False,
                    "error": f"Profile '{profile_id}' not found"
                })

            return json.dumps({
                "success": True,
                "action": "get",
                "profile": profile
            })

        elif action in ("create", "update"):
            if not profile_name or temperature is None or not phases:
                return json.dumps({
                    "success": False,
                    "error": "profile_name, temperature, and phases are required"
                })

            # Parse phases JSON
            try:
                phases_list = json.loads(phases)
            except json.JSONDecodeError:
                return json.dumps({
                    "success": False,
                    "error": "Invalid JSON in phases parameter"
                })

            # Validate phases structure
            if not isinstance(phases_list, list):
                return json.dumps({
                    "success": False,
                    "error": "phases must be a JSON array"
                })

            if len(phases_list) == 0:
                return json.dumps({
                    "success": False,
                    "error": "At least one phase is required"
                })

            # Validate each phase has required fields
            for idx, phase in enumerate(phases_list):
                if not isinstance(phase, dict):
                    return json.dumps({
                        "success": False,
                        "error": f"Phase {idx} must be an object"
                    })

                # Check required fields
                required_fields = ["name", "phase", "duration"]
                missing = [f for f in required_fields if f not in phase]
                if missing:
                    return json.dumps({
                        "success": False,
                        "error": f"Phase {idx} missing required fields: {', '.join(missing)}"
                    })

                # Validate duration is a number
                if not isinstance(phase["duration"], (int, float)):
                    return json.dumps({
                        "success": False,
                        "error": f"Phase {idx} 'duration' must be a number"
                    })

            # For update, use provided profile_id; for create, find existing by name
            target_id = profile_id
            if action == "update" and not target_id:
                existing = await ws_client.find_profile_by_label(profile_name)
                if existing:
                    target_id = existing.get("id")

            # Create or update profile
            saved_profile = await ws_client.create_or_update_profile(
                label=profile_name,
                temperature=temperature,
                phases=phases_list,
                profile_id=target_id
            )

            # Save version locally
            version_info = profile_storage.save_profile_version(
                profile_name=profile_name,
                profile_data=saved_profile,
                metadata={
                    "action": action,
                    "temperature": temperature,
                    "phase_count": len(phases_list)
                }
            )

            return json.dumps({
                "success": True,
                "action": action,
                "profile": saved_profile,
                "version_info": version_info
            })

        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown action '{action}'. Use: list, get, create, update"
            })

    except GaggimateError as e:
        logger.error("manage_profile_error", action=action, error=str(e), code=e.code.value)
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_code": e.code.value,
            "suggestion": _get_error_suggestion(e)
        })
    except Exception as e:
        logger.error("manage_profile_unexpected_error", action=action, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })


@mcp.tool()
async def analyze_shot(shot_id: str) -> str:
    """Get comprehensive shot analysis.

    Args:
        shot_id: Shot ID to analyze (will be normalized to 6 digits)

    Returns:
        JSON string with shot analysis
    """
    # Normalize shot ID to 6 digits for consistent lookups
    normalized_id = shot_id.zfill(6)
    logger.info("analyze_shot_called", shot_id=shot_id, normalized_id=normalized_id)

    try:
        # Fetch shot data with normalized ID
        shot_data = await http_client.fetch_shot(normalized_id)
        if not shot_data:
            return json.dumps({
                "success": False,
                "error": f"Shot '{shot_id}' not found"
            })

        # Transform for AI analysis
        transformed = transform_shot_for_ai(shot_data)

        # Get rating if available (using normalized ID)
        rating_data = rating_storage.get_rating(normalized_id)

        return json.dumps({
            "success": True,
            "shot": transformed,
            "rating": rating_data,
            "incomplete": shot_data.incomplete
        })

    except GaggimateError as e:
        logger.error("analyze_shot_error", shot_id=shot_id, error=str(e), code=e.code.value)
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_code": e.code.value,
            "suggestion": _get_error_suggestion(e)
        })
    except Exception as e:
        logger.error("analyze_shot_unexpected_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })


@mcp.tool()
async def manage_shot_notes(
    shot_id: str,
    action: str = "update",
    rating: Optional[int] = None,
    notes: Optional[str] = None,
    balance_taste: Optional[str] = None,
    grind_setting: Optional[str] = None,
    dose_in: Optional[float] = None,
    dose_out: Optional[float] = None,
    sync_to_device: bool = True
) -> str:
    """Manage shot notes and ratings.

    This tool saves feedback to both the Gaggimate device (via WebSocket API)
    and locally for backup/reference.

    Args:
        shot_id: Shot ID (e.g., "100" or "000100" - will be normalized)
        action: Action to perform - "update", "get", or "get_device" (default: "update")
        rating: Star rating (0-5, optional)
        notes: Tasting notes (optional)
        balance_taste: Taste balance - "bitter", "balanced", or "sour" (optional)
        grind_setting: Grinder setting used (optional)
        dose_in: Coffee dose in grams (optional)
        dose_out: Espresso output in grams (optional)
        sync_to_device: Whether to sync to Gaggimate device (default: True)

    Returns:
        JSON string with result
    """
    # Normalize shot ID - remove leading zeros for API, keep padded for local storage
    try:
        shot_id_int = int(shot_id)
        api_id = str(shot_id_int)  # For WebSocket API: "100"
        storage_id = str(shot_id_int).zfill(6)  # For local storage: "000100"
    except ValueError:
        return json.dumps({
            "success": False,
            "error": f"Invalid shot ID: '{shot_id}'. Must be a number."
        })

    logger.info("manage_shot_notes_called", shot_id=shot_id, api_id=api_id, storage_id=storage_id, action=action, rating=rating)

    try:
        if action == "get":
            # Get from local storage
            rating_data = rating_storage.get_rating(storage_id)
            if not rating_data:
                return json.dumps({
                    "success": True,
                    "shot_id": storage_id,
                    "rating": None,
                    "message": "No local notes found for this shot"
                })

            return json.dumps({
                "success": True,
                "shot_id": storage_id,
                "rating": rating_data,
                "source": "local"
            })

        elif action == "get_device":
            # Get from device via WebSocket
            device_notes = await ws_client.get_shot_notes(api_id)
            return json.dumps({
                "success": True,
                "shot_id": api_id,
                "notes": device_notes,
                "source": "device"
            })

        elif action == "update":
            results = {
                "device_synced": False,
                "local_saved": False,
                "device_error": None
            }

            # Add agent prefix to notes if provided
            agent_notes = None
            if notes:
                agent_prefix = "Updated by [llm agent]: "
                # Only add prefix if not already present
                if not notes.startswith(agent_prefix):
                    agent_notes = f"{agent_prefix}{notes}"
                else:
                    agent_notes = notes
            
            # Save to device if requested
            if sync_to_device:
                try:
                    await ws_client.save_shot_notes(
                        shot_id=api_id,
                        rating=rating,
                        notes=agent_notes,
                        balance_taste=balance_taste,
                        grind_setting=grind_setting,
                        dose_in=dose_in,
                        dose_out=dose_out,
                    )
                    results["device_synced"] = True
                    logger.info("shot_notes_synced_to_device", shot_id=api_id)
                except GaggimateError as e:
                    results["device_error"] = str(e)
                    logger.warning("shot_notes_device_sync_failed", shot_id=api_id, error=str(e))

            # Convert balance_taste string to enum if provided
            balance_taste_enum = None
            if balance_taste:
                try:
                    balance_taste_enum = BalanceTaste(balance_taste.lower())
                except ValueError:
                    logger.warning("invalid_balance_taste", value=balance_taste)
                    # Continue with None

            # Always save locally as backup
            shot_rating = ShotRating(
                shot_id=storage_id,
                rating=rating,
                notes=agent_notes,
                balance_taste=balance_taste_enum,
                grind_setting=grind_setting,
                dose_in=dose_in,
                dose_out=dose_out,
            )
            rating_data = rating_storage.save_rating(shot_rating)
            results["local_saved"] = True

            # Build response message
            if results["device_synced"]:
                message = "Shot notes saved to device and stored locally"
            elif results["device_error"]:
                message = f"Shot notes stored locally (device sync failed: {results['device_error']})"
            else:
                message = "Shot notes stored locally only"

            return json.dumps({
                "success": True,
                "message": message,
                "shot_id": storage_id,
                "api_id": api_id,
                "rating": rating_data,
                "sync_status": results
            })

        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown action '{action}'. Use 'update', 'get', or 'get_device'"
            })

    except ValidationError as e:
        # Pydantic validation error
        logger.error("manage_shot_notes_validation_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Validation error: {str(e)}"
        })
    except ValueError as e:
        # Other value errors
        logger.error("manage_shot_notes_value_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Value error: {str(e)}"
        })
    except Exception as e:
        logger.error("manage_shot_notes_unexpected_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })


@mcp.tool()
async def diagnose_connection() -> str:
    """Run connection diagnostics to troubleshoot device connectivity issues.

    This tool checks:
    - Device reachability (ping)
    - HTTP port accessibility
    - API endpoint availability
    - HTTPS misconfiguration
    - Network latency issues

    Returns:
        JSON string with diagnostic results and troubleshooting recommendations
    """
    logger.info("diagnose_connection_called")

    try:
        results = await run_diagnostics(config)

        # Format for user-friendly output
        summary = {
            "status": results["overall_status"],
            "host": results["host"],
            "tests": results["tests"],
            "issues": results["issues"],
            "recommendations": results["recommendations"]
        }

        return json.dumps({
            "success": True,
            "diagnostics": summary
        }, indent=2)

    except Exception as e:
        logger.error("diagnose_connection_error", error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Diagnostics failed: {str(e)}"
        })


@mcp.tool()
async def list_recent_shots(limit: int = 10) -> str:
    """List recent shots with optional filtering.

    Args:
        limit: Number of shots to return (default 10, max 50)

    Returns:
        JSON string with list of recent shots
    """
    logger.info("list_recent_shots_called", limit=limit)

    try:
        # Clamp limit
        limit = max(1, min(limit, 50))

        # Fetch shot index
        shots = await http_client.list_recent_shots(limit=limit)

        # Enrich with ratings
        for shot in shots:
            shot_id = shot["id"]
            rating_data = rating_storage.get_rating(shot_id)
            if rating_data:
                shot["user_rating"] = rating_data.get("rating")
                shot["user_notes"] = rating_data.get("notes")

        return json.dumps({
            "success": True,
            "shots": shots,
            "count": len(shots),
            "limit": limit
        })

    except GaggimateError as e:
        logger.error("list_recent_shots_error", limit=limit, error=str(e), code=e.code.value)
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_code": e.code.value,
            "suggestion": _get_error_suggestion(e)
        })
    except Exception as e:
        logger.error("list_recent_shots_unexpected_error", limit=limit, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })
