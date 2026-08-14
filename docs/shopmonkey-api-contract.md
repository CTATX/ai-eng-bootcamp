# ShopMonkey API contract

**Mode:** integration only. **Reskin:** not allowed.

Official docs: [shopmonkey.dev](https://shopmonkey.dev/overview)  
Legal: [Terms](https://www.shopmonkey.io/legal/terms-of-service) · [Acceptable use](https://www.shopmonkey.io/legal/acceptable-use-policy)

## What this repo does

Our FastAPI server calls ShopMonkey REST v3 (`https://api.shopmonkey.cloud/v3`) with a Bearer API key. Streamlit is our UI. We do not frame, restyle, or white-label the ShopMonkey product.

## Allowed

| Resource | Path | Use |
|----------|------|-----|
| Auth | `/v3/auth/api_key/status` | Verify the key |
| Customers | `/v3/customer`, `/v3/customer/search` | CRM records |
| Vehicles | `/v3/vehicle` | VIN, plate, mileage |
| Orders | `/v3/order` | Estimates and work orders |
| Appointments | `/v3/appointment` | Scheduling |
| Inventory | `/v3/inventory_part` | Parts and tires |
| Payments | `/v3/integration/payment` | Manual payments |
| Inspections | `/v3/inspection` | DVIs |
| Users | `/v3/user` | Employees; keys inherit creator permissions |
| Timeclock | `/v3/timesheet` | Clock in/out |
| Company | `/v3/company/:id` | Name/logo on *their* docs |
| Webhooks | `/v3/webhook` | Event push |

API + webhooks are on every ShopMonkey plan. Admin path: **Settings → Integration → API Keys**.

## Not allowed

- Reskin, frame, mirror, or clone the ShopMonkey UI
- Copy features/graphics into a competing product
- White-label or resell ShopMonkey access
- Scrape the web/mobile app
- Reverse engineer or bypass rate limits
- Enterprise Data Streaming without entitlement

`whiteLabelBlobId` on company config is ShopMonkey’s internal field, not a grant to rebrand their product.

## Local wiring

```bash
# .env — never commit
SHOPMONKEY_API_KEY=your-shopmonkey-key
```

| Method | Path | Needs key |
|--------|------|-----------|
| GET | `/shopmonkey/catalog` | No |
| GET | `/shopmonkey/status` | Yes to connect |
| GET | `/shopmonkey/snapshot?limit=25` | Yes |

Streamlit: sidebar → **ShopMonkey**.
