#!/usr/bin/env python3
"""MCP server exposing Intapp Open APIs."""

import json
import os

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from intapp_client import IntappClient

load_dotenv()

_client = IntappClient(
    token_url=os.environ["INTAPP_TOKEN_URL"],
    client_id=os.environ["INTAPP_CLIENT_ID"],
    client_secret=os.environ["INTAPP_CLIENT_SECRET"],
    base_url=os.environ["INTAPP_BASE_URL"],
)

_BLACKBOOK_TYPES_PATH = "api/common/v1/blackbookTypes"

app = Server("intapp-open")

_BLACKBOOK_TYPE_SCHEMA = {
    "type": "object",
    "properties": {
        "key": {"type": "string", "description": "Unique key for the blackbook type."},
        "name": {"type": "string", "description": "Display name."},
        "active": {"type": "boolean", "description": "Whether the type is active."},
        "sortOrder": {"type": "integer", "description": "Sort order position."},
    },
    "required": ["key", "name"],
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_blackbook_types",
            description="List all blackbook types from Intapp Open (GET /api/common/v1/blackbookTypes).",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="create_blackbook_type",
            description="Create a new blackbook type (POST /api/common/v1/blackbookTypes).",
            inputSchema={
                "type": "object",
                "properties": _BLACKBOOK_TYPE_SCHEMA["properties"],
                "required": _BLACKBOOK_TYPE_SCHEMA["required"],
            },
        ),
        Tool(
            name="update_blackbook_type",
            description="Update one or more existing blackbook types (PATCH /api/common/v1/blackbookTypes). Pass a list of objects with the fields to change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "types": {
                        "type": "array",
                        "description": "Array of blackbook type objects to patch.",
                        "items": _BLACKBOOK_TYPE_SCHEMA,
                    }
                },
                "required": ["types"],
            },
        ),
        Tool(
            name="bulk_create_blackbook_types",
            description="Bulk-create multiple blackbook types in one call (POST /api/common/v1/blackbookTypes/_bulk).",
            inputSchema={
                "type": "object",
                "properties": {
                    "types": {
                        "type": "array",
                        "description": "Array of blackbook type objects to create.",
                        "items": _BLACKBOOK_TYPE_SCHEMA,
                    }
                },
                "required": ["types"],
            },
        ),
        # Generic escape hatches for any other Intapp Open endpoint
        Tool(
            name="intapp_get",
            description="Perform a GET request against any Intapp Open API endpoint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to the base URL."},
                    "params": {
                        "type": "object",
                        "description": "Optional query parameters.",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="intapp_post",
            description="Perform a POST request against any Intapp Open API endpoint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path relative to the base URL."},
                    "body": {"type": "object", "description": "JSON request body."},
                },
                "required": ["path", "body"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_blackbook_types":
            result = await _client.get(_BLACKBOOK_TYPES_PATH)

        elif name == "create_blackbook_type":
            result = await _client.post(_BLACKBOOK_TYPES_PATH, arguments)

        elif name == "update_blackbook_type":
            result = await _client.patch(_BLACKBOOK_TYPES_PATH, arguments["types"])

        elif name == "bulk_create_blackbook_types":
            result = await _client.post(f"{_BLACKBOOK_TYPES_PATH}/_bulk", arguments["types"])

        elif name == "intapp_get":
            result = await _client.get(arguments["path"], arguments.get("params"))

        elif name == "intapp_post":
            result = await _client.post(arguments["path"], arguments["body"])

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as exc:
        return [TextContent(type="text", text=f"Error: {exc}")]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
