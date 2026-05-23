# SAM.gov MCP Server

**Federal contracting intelligence for AI assistants.**

🌐 **[Live site → algoevolved.github.io/samgov-mcp-server](https://algoevolved.github.io/samgov-mcp-server/)**

Connects Claude (and any MCP-compatible AI) to SAM.gov, USASpending.gov, and SBIR.gov. Search $700B+ in annual federal contracts, find expiring recompetes, and profile your competition — all in plain English.

## Tools

| Tool | Description |
|------|-------------|
| `search_opportunities` | Search active solicitations by keyword, agency, NAICS, set-aside |
| `get_opportunity_details` | Full detail for a single opportunity by Notice ID |
| `search_awards` | Historical contract awards — who won what, for how much |
| `get_vendor_profile` | SAM.gov entity registration, certifications, CAGE/UEI lookup |
| `find_expiring_contracts` | Recompete intelligence — contracts ending in next N days |
| `analyze_agency_spending` | Agency spend breakdown, top vendors, budget patterns |
| `search_grants_sbir` | SBIR/STTR non-dilutive grant solicitations and award history |
| `get_competitive_landscape` | Who's winning in a market segment — concentration, avg contract size |

## Quick Start

```bash
git clone https://github.com/algoevolved/samgov-mcp-server.git
cd samgov-mcp-server
cp .env.example .env
# Edit .env — set SAM_API_KEY and DEV_MODE=true
docker compose up --build
```

Health check: `curl http://localhost:8080/health`

## Connect to Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "samgov": {
      "url": "https://samgov-mcp-server-production.up.railway.app/sse",
      "headers": {
        "x-api-key": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

## Pricing

| Tier | Price | Daily Requests |
|------|-------|----------------|
| Solo | $79/mo | 500 |
| Team | $199/mo | 2,000 |
| Enterprise | $499/mo | 10,000 |

7-day free trial on all plans. → [Get started](https://algoevolved.github.io/samgov-mcp-server/#pricing)

## License

MIT
