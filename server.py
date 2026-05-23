"""
SAM.gov MCP Server — SSE transport entrypoint.

Runs as a persistent HTTP server. Customers configure it as a remote MCP server
in their Claude Desktop config:

  "samgov": {
    "url": "https://your-deployed-url.railway.app/sse",
    "headers": { "x-api-key": "smgov_their_key_here" }
  }

During local dev (DEV_MODE=true), no auth is required.
"""

import asyncio
import structlog
import uvicorn

from mcp.server.sse import SseServerTransport
from mcp import types
from mcp.server import Server
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route, Mount

from config import settings
from middleware.auth import validate_request

from tools.search_opportunities import SCHEMA as SEARCH_OPP_SCHEMA, run as search_opportunities
from tools.get_opportunity_details import SCHEMA as OPP_DETAIL_SCHEMA, run as get_opportunity_details
from tools.search_awards import SCHEMA as SEARCH_AWARDS_SCHEMA, run as search_awards
from tools.get_vendor_profile import SCHEMA as VENDOR_SCHEMA, run as get_vendor_profile
from tools.find_expiring_contracts import SCHEMA as EXPIRING_SCHEMA, run as find_expiring_contracts
from tools.analyze_agency_spending import SCHEMA as SPENDING_SCHEMA, run as analyze_agency_spending
from tools.search_grants_sbir import SCHEMA as SBIR_SCHEMA, run as search_grants_sbir
from tools.get_competitive_landscape import SCHEMA as LANDSCAPE_SCHEMA, run as get_competitive_landscape

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

ALL_TOOLS = [
    SEARCH_OPP_SCHEMA, OPP_DETAIL_SCHEMA, SEARCH_AWARDS_SCHEMA, VENDOR_SCHEMA,
    EXPIRING_SCHEMA, SPENDING_SCHEMA, SBIR_SCHEMA, LANDSCAPE_SCHEMA,
]

TOOL_REGISTRY = {
    "search_opportunities": search_opportunities,
    "get_opportunity_details": get_opportunity_details,
    "search_awards": search_awards,
    "get_vendor_profile": get_vendor_profile,
    "find_expiring_contracts": find_expiring_contracts,
    "analyze_agency_spending": analyze_agency_spending,
    "search_grants_sbir": search_grants_sbir,
    "get_competitive_landscape": get_competitive_landscape,
}

mcp = Server(settings.SERVER_NAME)

@mcp.list_tools()
async def list_tools() -> list[types.Tool]:
    return ALL_TOOLS

@mcp.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    logger.info("tool_call", tool=name)
    if settings.BILLING_ENABLED and not settings.DEV_MODE:
        api_key = arguments.pop("__api_key", None)
        auth_result = await validate_request(api_key=api_key, tool_name=name)
        if not auth_result.ok:
            return [types.TextContent(type="text", text=f"❌ Auth error: {auth_result.message}")]
    handler = TOOL_REGISTRY.get(name)
    if handler is None:
        return [types.TextContent(type="text", text=f"❌ Unknown tool: {name}")]
    try:
        result = await handler(**arguments)
        return [types.TextContent(type="text", text=result)]
    except Exception as exc:
        logger.exception("tool_error", tool=name, error=str(exc))
        return [types.TextContent(type="text", text=f"❌ Error in {name}: {type(exc).__name__}: {exc}")]

sse = SseServerTransport("/messages/")

async def handle_sse(request: Request) -> Response:
    if settings.BILLING_ENABLED and not settings.DEV_MODE:
        api_key = request.headers.get("x-api-key")
        auth = await validate_request(api_key=api_key, tool_name="__connect__")
        if not auth.ok:
            return JSONResponse({"error": auth.message}, status_code=401)
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await mcp.run(streams[0], streams[1], mcp.create_initialization_options())
    return Response()

async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "version": settings.SERVER_VERSION,
                        "tools": len(ALL_TOOLS), "dev_mode": settings.DEV_MODE})

app = Starlette(routes=[
    Route("/health", health),
    Route("/sse", handle_sse),
    Mount("/messages/", app=sse.handle_post_message),
])

if __name__ == "__main__":
    logger.info("samgov_mcp_starting", version=settings.SERVER_VERSION, tools=len(ALL_TOOLS),
                host=settings.SERVER_HOST, port=settings.SERVER_PORT,
                billing=settings.BILLING_ENABLED, dev_mode=settings.DEV_MODE)
    uvicorn.run(app, host=settings.SERVER_HOST, port=settings.SERVER_PORT,
                log_level=settings.LOG_LEVEL.lower())
