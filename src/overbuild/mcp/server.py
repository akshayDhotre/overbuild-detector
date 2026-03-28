"""
MCP server exposing OverBuild analysis as a tool.

Run:
    python -m overbuild.mcp.server
"""

import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from overbuild.api.models import AnalyzeRequest
from overbuild.core.pipeline import analyze

server = Server("overbuild-detector")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="check_before_building",
            description=(
                "Before writing new code, check if existing tools, packages, or one-liners "
                "already solve the problem."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "problem": {"type": "string", "description": "What you're planning to build"},
                    "language": {"type": "string", "description": "Target language"},
                    "context": {"type": "string", "description": "Constraints and environment"},
                },
                "required": ["problem"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, object]) -> list[TextContent]:
    if name != "check_before_building":
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    request = AnalyzeRequest(**arguments)
    result = await analyze(request)
    lines = [
        "## OverBuild Analysis",
        "",
        f"**Verdict: {result.verdict.value}**",
        f"**OverBuild Score: {result.overbuild_score.score}** ({result.overbuild_score.explanation})",
        "",
        result.summary,
    ]
    if result.one_liner:
        lines.extend(["", "### One-Liner", "```", result.one_liner, "```"])
    if result.existing_solutions:
        lines.append("")
        lines.append("### Existing Solutions")
        for index, solution in enumerate(result.existing_solutions[:3], start=1):
            lines.append(f"{index}. **{solution.name}** - {solution.description}")
            lines.append(f"   URL: {solution.url}")
            if solution.install_command:
                lines.append(f"   Install: `{solution.install_command}`")
    if result.if_you_must_build:
        lines.extend(["", "### If You Must Build", result.if_you_must_build])

    return [TextContent(type="text", text="\n".join(lines))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
