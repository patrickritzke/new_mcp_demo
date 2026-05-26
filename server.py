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

app = Server("intapp-open")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="intapp_get",
            description="Perform a GET request against an Intapp Open API endpoint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "API path relative to the base URL, e.g. 'entities/matters'.",
                    },
                    "params": {
                        "type": "object",
                        "description": "Optional query parameters as key/value pairs.",
                        "additionalProperties": {"type": "string"},
                    },
                },
                "required": ["path"],
            },
        ),
        Tool(
            name="intapp_post",
            description="Perform a POST request against an Intapp Open API endpoint.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "API path relative to the base URL.",
                    },
                    "body": {
                        "type": "object",
                        "description": "JSON body to send with the request.",
                    },
                },
                "required": ["path", "body"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "intapp_get":
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
