# SAM.gov MCP Server

Federal contracting intelligence for AI assistants. Connects Claude (and any MCP-compatible AI) to SAM.gov, USASpending.gov, and SBIR.gov.

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
      "url": "https://your-railway-url.railway.app/sse"
    }
  }
}
```

## Pricing Tiers

| Tier | Price | Daily Requests |
|------|-------|----------------|
| Solo | $79/mo | 500 |
| Team | $199/mo | 2,000 |
| Enterprise | $499/mo | 10,000 |

7-day free trial on all plans.

## License

MIT
