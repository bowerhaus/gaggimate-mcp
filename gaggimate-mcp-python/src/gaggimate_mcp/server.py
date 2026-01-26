"""MCP server for Gaggimate espresso machine."""

#!/usr/bin/env python3

from mcp.server import Server
from gaggimate_mcp.config import GaggimateConfig
from gaggimate_mcp.logging_config import setup_logging, get_logger


# Initialize configuration and logging
config = GaggimateConfig()
setup_logging(log_level=config.log_level)
logger = get_logger(__name__)

# Create MCP server
app = Server("gaggimate-mcp")


@app.list_tools()
async def list_tools():
    """List available MCP tools."""
    return [
        {
            "name": "manage_profile",
            "description": "Manage espresso brewing profiles (list, get, create, update)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["list", "get", "create", "update"],
                        "description": "Action to perform"
                    }
                },
                "required": ["action"]
            }
        },
        {
            "name": "analyze_shot",
            "description": "Get comprehensive shot analysis with context",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "shot_id": {
                        "type": "string",
                        "description": "Shot ID to analyze"
                    }
                },
                "required": ["shot_id"]
            }
        },
        {
            "name": "record_shot_feedback",
            "description": "Record or update shot rating and tasting notes",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "shot_id": {
                        "type": "string",
                        "description": "Shot ID to rate"
                    },
                    "rating": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 5,
                        "description": "Star rating (0-5)"
                    }
                },
                "required": ["shot_id"]
            }
        },
        {
            "name": "list_recent_shots",
            "description": "List recent shots with optional filtering",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "maximum": 50,
                        "description": "Number of shots to return"
                    }
                }
            }
        },
        {
            "name": "dial_in_assistant",
            "description": "Stateful workflow orchestration for guided bean dialing",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start_session", "record_shot", "suggest_adjustment", "apply_adjustment", "end_session"],
                        "description": "Workflow step"
                    }
                },
                "required": ["action"]
            }
        }
    ]


async def main():
    """Run the MCP server."""
    logger.info(
        "starting_mcp_server",
        host=config.gaggimate_host,
        protocol=config.gaggimate_protocol
    )

    # Server will be started by mcp run command
    # This is just the initialization
    logger.info("mcp_server_ready")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
