"""MCP server for Gaggimate espresso machine."""

#!/usr/bin/env python3

import json
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
from gaggimate_mcp.models.rating import ShotRating
from gaggimate_mcp.errors import GaggimateError


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
        logger.error("manage_profile_error", action=action, error=str(e))
        return json.dumps({
            "success": False,
            "error": str(e),
            "code": e.code.value
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
        logger.error("analyze_shot_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": str(e),
            "code": e.code.value
        })
    except Exception as e:
        logger.error("analyze_shot_unexpected_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })


@mcp.tool()
async def update_feedback(
    shot_id: str,
    rating: Optional[int] = None,
    notes: Optional[str] = None
) -> str:
    """Update shot rating and tasting notes.

    Args:
        shot_id: Shot ID to rate (will be normalized to 6 digits)
        rating: Star rating (0-5, optional)
        notes: Tasting notes (optional)

    Returns:
        JSON string with confirmation
    """
    # Normalize shot ID to 6 digits for consistent storage
    normalized_id = shot_id.zfill(6)
    logger.info("update_feedback_called", shot_id=shot_id, normalized_id=normalized_id, rating=rating)

    try:
        # Create rating object with normalized ID
        shot_rating = ShotRating(
            shot_id=normalized_id,
            rating=rating,
            notes=notes
        )

        # Save rating
        rating_data = rating_storage.save_rating(shot_rating)

        return json.dumps({
            "success": True,
            "message": "Feedback recorded successfully",
            "rating": rating_data
        })

    except ValidationError as e:
        # Pydantic validation error
        logger.error("update_feedback_validation_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Validation error: {str(e)}"
        })
    except ValueError as e:
        # Other value errors
        logger.error("update_feedback_value_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Value error: {str(e)}"
        })
    except Exception as e:
        logger.error("update_feedback_unexpected_error", shot_id=shot_id, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
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
        logger.error("list_recent_shots_error", limit=limit, error=str(e))
        return json.dumps({
            "success": False,
            "error": str(e),
            "code": e.code.value
        })
    except Exception as e:
        logger.error("list_recent_shots_unexpected_error", limit=limit, error=str(e))
        return json.dumps({
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        })
