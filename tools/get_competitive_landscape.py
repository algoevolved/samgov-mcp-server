import datetime
from mcp.types import Tool
from clients.usaspending_client import search_awards as _search, get_recipient_awards as _recipient

SCHEMA = Tool(
    name="get_competitive_landscape",
    description="Analyze the competitive landscape for a market segment or agency. Shows incumbents, award history, contract sizes, and win concentration. Use before pursuing new opportunities.",
    inputSchema={"type": "object", "properties": {
        "market_keywords": {"type": "array", "items": {"type": "string"}},
        "agency_name": {"type": "string"}, "competitor_name": {"type": "string"},
        "years_back": {"type": "integer", "default": 3, "minimum": 1, "maximum": 10},
        "limit": {"type": "integer", "default": 25, "minimum": 5, "maximum": 100},
    }},
)

async def run(market_keywords=None, agency_name=None, competitor_name=None, years_back=3, limit=25):
    start = (datetime.date.today() - datetime.timedelta(days=365*years_back)).isoformat()
    if competitor_name:
        data = await _recipient(recipient_name=competitor_name, limit=limit)
        results = data.get("results", [])
        total = data.get("page_metadata", {}).get("total", 0)
        tv = sum(r.get("Award Amount", 0) or 0 for r in results)
        lines = [f"# {competitor_name}\n{total:,} awards | ${tv:,.0f}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. ${r.get('Award Amount',0):,.0f} — {r.get('Awarding Agency','?')}\n   {(r.get('Description') or '')[:100]}\n   {r.get('Start Date','?')} → {r.get('End Date','?')}\n")
        return "\n".join(lines)
    data = await _search(keywords=market_keywords, agency_name=agency_name, start_date=start, limit=limit)
    results = data.get("results", [])
    if not results: return "No awards found."
    by_v = {}
    for r in results:
        n = r.get("Recipient Name", "?")
        a = r.get("Award Amount", 0) or 0
        if n not in by_v: by_v[n] = {"total": 0, "count": 0}
        by_v[n]["total"] += a; by_v[n]["count"] += 1
    sv = sorted(by_v.items(), key=lambda x: x[1]["total"], reverse=True)
    gt = sum(v["total"] for _, v in sv)
    total = data.get("page_metadata", {}).get("total", 1)
    lines = [f"# Competitive Landscape" + (f": {market_keywords}" if market_keywords else "") + (f" @ {agency_name}" if agency_name else "") + f"\n{total:,} awards | ${gt:,.0f} | Last {years_back}yr\n"]
    for i, (n, s) in enumerate(sv[:15], 1):
        pct = s["total"]/gt*100 if gt else 0
        lines.append(f"{i:2}. {n}: ${s['total']:,.0f} ({pct:.1f}%) | {s['count']} awards")
    top3 = sum(v["total"] for _, v in sv[:3])/gt*100 if gt else 0
    lines.append(f"\nTop 3: {top3:.0f}% | Avg: ${gt/total:,.0f} | {len(by_v)} vendors")
    return "\n".join(lines)
