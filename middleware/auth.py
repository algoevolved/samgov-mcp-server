import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Literal
import stripe
import structlog
from config import settings

logger = structlog.get_logger()
Tier = Literal["solo", "team", "enterprise"]
_rate_buckets: dict = {}
_TIER_LIMITS = {
    "solo": settings.RATE_LIMIT_SOLO,
    "team": settings.RATE_LIMIT_TEAM,
    "enterprise": settings.RATE_LIMIT_ENTERPRISE,
}


@dataclass
class AuthResult:
    ok: bool
    message: str = ""
    tier: str | None = None
    customer_id: str | None = None


async def validate_request(api_key, tool_name):
    if settings.DEV_MODE:
        if api_key == settings.DEV_API_KEY:
            return AuthResult(ok=True, tier="enterprise", customer_id="dev")
        return AuthResult(ok=False, message="Invalid dev API key")
    if not api_key:
        return AuthResult(ok=False, message="Missing API key.")
    customer = await _lookup_customer(api_key)
    if customer is None:
        return AuthResult(ok=False, message="Invalid API key.")
    tier = customer.get("tier", "solo")
    sub_status = customer.get("subscription_status", "inactive")
    if sub_status not in ("active", "trialing"):
        return AuthResult(ok=False, message=f"Subscription is {sub_status}.")
    rate_ok, used, limit = _check_rate_limit(api_key, tier)
    if not rate_ok:
        return AuthResult(ok=False, message=f"Rate limit exceeded ({used}/{limit} req/day).")
    return AuthResult(ok=True, tier=tier, customer_id=customer.get("id"))


async def _lookup_customer(api_key):
    if not settings.STRIPE_SECRET_KEY:
        return None
    stripe.api_key = settings.STRIPE_SECRET_KEY
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    try:
        customers = stripe.Customer.search(query=f'metadata["api_key_hash"]:"{key_hash}"')
        if not customers.data:
            return None
        customer = customers.data[0]
        subs = stripe.Subscription.list(customer=customer.id, status="all", limit=1)
        tier, sub_status = "solo", "inactive"
        if subs.data:
            sub = subs.data[0]
            sub_status = sub.status
            price_id = sub["items"]["data"][0]["price"]["id"]
            if price_id == settings.STRIPE_PRICE_ENTERPRISE:
                tier = "enterprise"
            elif price_id == settings.STRIPE_PRICE_TEAM:
                tier = "team"
        return {"id": customer.id, "email": customer.email, "tier": tier, "subscription_status": sub_status}
    except stripe.StripeError as exc:
        logger.error("stripe_lookup_error", error=str(exc))
        return None


def _check_rate_limit(api_key, tier):
    limit = _TIER_LIMITS.get(tier, settings.RATE_LIMIT_SOLO)
    today = int(time.time()) // 86400
    key = f"{api_key}:{today}"
    bucket = _rate_buckets.get(key, {"count": 0, "day": today})
    if len(_rate_buckets) > 10000:
        for k in [k for k in _rate_buckets if _rate_buckets[k]["day"] < today]:
            del _rate_buckets[k]
    current = bucket["count"]
    if current >= limit:
        return False, current, limit
    bucket["count"] = current + 1
    _rate_buckets[key] = bucket
    return True, current + 1, limit


async def _send_api_key_email(to_email: str, api_key: str, tier: str) -> None:
    """Send the customer their API key via Resend. Silently skips if RESEND_API_KEY not set."""
    if not settings.RESEND_API_KEY:
        logger.warning("resend_key_missing", msg="RESEND_API_KEY not set — skipping email")
        return

    try:
        import resend  # type: ignore
        resend.api_key = settings.RESEND_API_KEY

        tier_limits = {"solo": "500", "team": "2,000", "enterprise": "10,000"}
        daily_limit = tier_limits.get(tier, "500")

        resend.Emails.send({
            "from": f"SAM.gov MCP <{settings.EMAIL_FROM}>",
            "to": [to_email],
            "subject": "Your SAM.gov MCP API Key",
            "html": f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0e1a;color:#e2e8f0;padding:40px;">
  <div style="max-width:560px;margin:0 auto;">
    <h1 style="color:#fff;font-size:1.5rem;margin-bottom:0.5rem;">Your SAM.gov MCP API Key</h1>
    <p style="color:#94a3b8;margin-bottom:2rem;">Welcome! Here's everything you need to connect Claude to federal contracting data.</p>

    <div style="background:#0d1117;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:1.25rem;margin-bottom:1.5rem;">
      <p style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">Your API Key ({tier.title()} — {daily_limit} req/day)</p>
      <code style="font-family:monospace;color:#4f8ef7;font-size:0.95rem;word-break:break-all;">{api_key}</code>
    </div>

    <p style="color:#94a3b8;font-size:0.9rem;margin-bottom:0.5rem;">Add this to your <code style="background:rgba(255,255,255,0.08);padding:2px 6px;border-radius:4px;color:#93c5fd;">claude_desktop_config.json</code>:</p>

    <div style="background:#0d1117;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:1.25rem;margin-bottom:2rem;">
      <pre style="font-family:monospace;font-size:0.82rem;color:#93c5fd;margin:0;overflow-x:auto;">&#123;
  &quot;mcpServers&quot;: &#123;
    &quot;samgov&quot;: &#123;
      &quot;url&quot;: &quot;https://samgov-mcp-server-production.up.railway.app/sse&quot;,
      &quot;headers&quot;: &#123;
        &quot;x-api-key&quot;: &quot;{api_key}&quot;
      &#125;
    &#125;
  &#125;
&#125;</pre>
    </div>

    <p style="color:#94a3b8;font-size:0.85rem;">Keep this key private — it's tied to your subscription. If you need to rotate it, reply to this email.</p>
    <p style="color:#64748b;font-size:0.8rem;margin-top:2rem;">SAM.gov MCP · <a href="https://algoevolved.github.io/samgov-mcp-server/" style="color:#4f8ef7;">Documentation</a> · <a href="mailto:aiquickhack@gmail.com" style="color:#4f8ef7;">Support</a></p>
  </div>
</body>
</html>
""",
        })
        logger.info("api_key_email_sent", to=to_email, tier=tier)
    except Exception as exc:
        logger.error("api_key_email_failed", error=str(exc), to=to_email)


async def handle_stripe_webhook(payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        return {"error": "Invalid signature"}

    stripe.api_key = settings.STRIPE_SECRET_KEY
    data = event["data"]["object"]

    if event["type"] == "customer.subscription.created":
        api_key = f"smgov_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Determine tier from price ID
        price_id = data["items"]["data"][0]["price"]["id"]
        if price_id == settings.STRIPE_PRICE_ENTERPRISE:
            tier = "enterprise"
        elif price_id == settings.STRIPE_PRICE_TEAM:
            tier = "team"
        else:
            tier = "solo"

        # Store hash in Stripe customer metadata
        customer = stripe.Customer.modify(
            data["customer"],
            metadata={"api_key_hash": key_hash},
        )

        # Email the key to the customer
        customer_email = customer.get("email") or ""
        if customer_email:
            await _send_api_key_email(customer_email, api_key, tier)
        else:
            logger.warning("no_customer_email", customer_id=data["customer"])

        logger.info("subscription_provisioned", customer=data["customer"], tier=tier)

    elif event["type"] == "customer.subscription.deleted":
        stripe.Customer.modify(data["customer"], metadata={"api_key_hash": ""})
        logger.info("subscription_cancelled", customer=data["customer"])

    elif event["type"] == "invoice.payment_failed":
        logger.warning("payment_failed", customer=data.get("customer"))

    return {"received": True}
