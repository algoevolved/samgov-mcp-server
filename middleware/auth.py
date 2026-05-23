import hashlib
import time
from dataclasses import dataclass
from typing import Literal
import stripe
import structlog
from config import settings

logger = structlog.get_logger()
Tier = Literal["solo", "team", "enterprise"]
_rate_buckets: dict = {}
_TIER_LIMITS = {"solo": settings.RATE_LIMIT_SOLO, "team": settings.RATE_LIMIT_TEAM, "enterprise": settings.RATE_LIMIT_ENTERPRISE}

@dataclass
class AuthResult:
    ok: bool
    message: str = ""
    tier: str | None = None
    customer_id: str | None = None

async def validate_request(api_key, tool_name):
    if settings.DEV_MODE:
        return AuthResult(ok=True, tier="enterprise", customer_id="dev") if api_key == settings.DEV_API_KEY else AuthResult(ok=False, message="Invalid dev API key")
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
    if not settings.STRIPE_SECRET_KEY: return None
    stripe.api_key = settings.STRIPE_SECRET_KEY
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    try:
        customers = stripe.Customer.search(query=f'metadata["api_key_hash"]:"{key_hash}"')
        if not customers.data: return None
        customer = customers.data[0]
        subs = stripe.Subscription.list(customer=customer.id, status="all", limit=1)
        tier, sub_status = "solo", "inactive"
        if subs.data:
            sub = subs.data[0]
            sub_status = sub.status
            price_id = sub["items"]["data"][0]["price"]["id"]
            if price_id == settings.STRIPE_PRICE_ENTERPRISE: tier = "enterprise"
            elif price_id == settings.STRIPE_PRICE_TEAM: tier = "team"
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
        for k in [k for k in _rate_buckets if _rate_buckets[k]["day"] < today]: del _rate_buckets[k]
    current = bucket["count"]
    if current >= limit: return False, current, limit
    bucket["count"] = current + 1
    _rate_buckets[key] = bucket
    return True, current + 1, limit

async def handle_stripe_webhook(payload, sig_header):
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except stripe.SignatureVerificationError:
        return {"error": "Invalid signature"}
    data = event["data"]["object"]
    if event["type"] == "customer.subscription.created":
        import secrets
        api_key = f"smgov_{secrets.token_urlsafe(32)}"
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Customer.modify(data["customer"], metadata={"api_key_hash": hashlib.sha256(api_key.encode()).hexdigest()})
    elif event["type"] == "customer.subscription.deleted":
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Customer.modify(data["customer"], metadata={"api_key_hash": ""})
    return {"received": True}
