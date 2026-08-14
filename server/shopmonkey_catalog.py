"""Public ShopMonkey REST v3 surfaces we integrate with — not a reskin grant."""

from __future__ import annotations

SHOPMONKEY_BASE_URL = "https://api.shopmonkey.cloud/v3"
SHOPMONKEY_DOCS_URL = "https://shopmonkey.dev/overview"
SHOPMONKEY_TOS_URL = "https://www.shopmonkey.io/legal/terms-of-service"
SHOPMONKEY_AUP_URL = "https://www.shopmonkey.io/legal/acceptable-use-policy"

INTEGRATION_MODE = "integration"
RESKIN_MODE = "reskin"

ALLOWED_RESOURCES = [
    {
        "name": "Auth",
        "path": "/v3/auth/api_key/status",
        "use": "Verify a Bearer API key.",
    },
    {
        "name": "Customers",
        "path": "/v3/customer and /v3/customer/search",
        "use": "Search and manage shop customers.",
    },
    {
        "name": "Vehicles",
        "path": "/v3/vehicle",
        "use": "VIN, plate, mileage, and ownership records.",
    },
    {
        "name": "Orders",
        "path": "/v3/order",
        "use": "Estimates and work orders, line items, PDFs.",
    },
    {
        "name": "Appointments",
        "path": "/v3/appointment",
        "use": "Create, list, confirm, and cancel appointments.",
    },
    {
        "name": "Inventory",
        "path": "/v3/inventory_part",
        "use": "Parts and tire stock assigned to orders.",
    },
    {
        "name": "Payments",
        "path": "/v3/integration/payment",
        "use": "Search and record manual payments.",
    },
    {
        "name": "Inspections",
        "path": "/v3/inspection",
        "use": "Digital vehicle inspections on an order.",
    },
    {
        "name": "Users",
        "path": "/v3/user",
        "use": "Employees and roles. Keys inherit the creating admin.",
    },
    {
        "name": "Timeclock",
        "path": "/v3/timesheet",
        "use": "Clock in/out against labor and orders.",
    },
    {
        "name": "Company",
        "path": "/v3/company/:id",
        "use": "Name and logo for ShopMonkey-generated docs. Not a white-label SDK.",
    },
    {
        "name": "Webhooks",
        "path": "/v3/webhook",
        "use": "Push Order, Customer, Vehicle, Payment, and related events.",
    },
]

NOT_ALLOWED = [
    {
        "action": "Reskin, frame, or mirror the ShopMonkey UI",
        "why": "ToS §2.2 forbids copying, framing, mirroring, or creating derivative works of the Services.",
    },
    {
        "action": "Copy ShopMonkey features, functions, or graphics into a clone",
        "why": "ToS §2.2(viii) and AUP I.D prohibit building a competing product from the Services.",
    },
    {
        "action": "White-label or resell ShopMonkey as your product",
        "why": "License is non-transferable and non-sublicensable; AUP I.D.d blocks resale/redistribution.",
    },
    {
        "action": "Scrape the web/mobile app instead of the official API",
        "why": "AUP I.G allows automated access only through official APIs and authorized integrations.",
    },
    {
        "action": "Reverse engineer or disable security / rate limits",
        "why": "ToS §2.2(i)(v) and AUP I.B.d.",
    },
    {
        "action": "Use Enterprise Data Streaming without entitlement",
        "why": "EDS is gated and requires a ShopMonkey sales conversation.",
    },
]

WEBHOOK_EVENTS = [
    "Appointment",
    "Customer",
    "Inspection",
    "Inventory",
    "Message",
    "Order",
    "Payment",
    "PurchaseOrder",
    "User",
    "Vehicle",
    "Vendor",
]


def catalog() -> dict:
    return {
        "mode": INTEGRATION_MODE,
        "reskin_allowed": False,
        "base_url": SHOPMONKEY_BASE_URL,
        "docs_url": SHOPMONKEY_DOCS_URL,
        "terms_url": SHOPMONKEY_TOS_URL,
        "acceptable_use_url": SHOPMONKEY_AUP_URL,
        "summary": (
            "Use ShopMonkey REST v3 to read and write shop data from our app. "
            "Do not restyle, iframe, or white-label the ShopMonkey product."
        ),
        "allowed_resources": ALLOWED_RESOURCES,
        "not_allowed": NOT_ALLOWED,
        "webhook_events": WEBHOOK_EVENTS,
    }
