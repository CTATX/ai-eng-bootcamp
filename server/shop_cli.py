"""CLI for Jake shop intelligence — status, ingest, hypothesis."""

from __future__ import annotations

import argparse
import json
import sys

from server.shop_hypothesis import build_hypothesis
from server.shop_ingest import ingest_orders, ingest_status
from server.shop_service import status as warehouse_status
from server.shop_synthetic import seed_if_empty
from server.shopmonkey_client import ShopmonkeyAPIError, api_key_configured, auth_status


def _print_json(payload: object) -> None:
    print(json.dumps(payload, indent=2, default=str))


def cmd_status(_: argparse.Namespace) -> int:
    seed_if_empty()
    payload = {
        "warehouse": warehouse_status(),
        "ingest": ingest_status(),
        "shopmonkey_key_configured": api_key_configured(),
    }
    if api_key_configured():
        try:
            payload["shopmonkey_auth"] = auth_status()
        except ShopmonkeyAPIError as exc:
            payload["shopmonkey_auth_error"] = {"status": exc.status_code, "message": exc.message}
    _print_json(payload)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    if not api_key_configured():
        print(
            "SHOPMONKEY_API_KEY missing. Add it to .env (Settings → Integration → API Keys in ShopMonkey).",
            file=sys.stderr,
        )
        return 1
    try:
        result = ingest_orders(page_size=args.page_size, max_pages=args.max_pages)
    except ShopmonkeyAPIError as exc:
        print(f"ShopMonkey error {exc.status_code}: {exc.message}", file=sys.stderr)
        return 1
    _print_json(result)
    return 0


def cmd_hypothesis(args: argparse.Namespace) -> int:
    seed_if_empty()
    payload = build_hypothesis(
        vin=args.vin,
        year=args.year,
        make=args.make,
        model=args.model,
        engine=args.engine,
        complaint=args.complaint,
        mileage=args.mileage,
    )
    if args.compact:
        summary = {
            "persona": payload["persona"],
            "vehicle": payload["vehicle_match"],
            "top_reason": payload["common_reasons"][:3],
            "likelihood": payload["likelihood"],
            "ticket": payload["ticket"],
            "time": payload["time"],
            "parts_count": len(payload["parts"]),
            "gotchas": payload["gotchas"],
        }
        _print_json(summary)
    else:
        _print_json(payload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Jake shop intelligence CLI — synthetic warehouse now, ShopMonkey when keyed."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    status_parser = sub.add_parser("status", help="Warehouse + ingest + key status")
    status_parser.set_defaults(func=cmd_status)

    ingest_parser = sub.add_parser("ingest", help="Pull ShopMonkey orders into warehouse")
    ingest_parser.add_argument("--page-size", type=int, default=25)
    ingest_parser.add_argument("--max-pages", type=int, default=None)
    ingest_parser.set_defaults(func=cmd_ingest)

    hyp_parser = sub.add_parser("hypothesis", help="Jake data-based hypothesis (no LLM)")
    hyp_parser.add_argument("--vin", default=None)
    hyp_parser.add_argument("--year", type=int, default=None)
    hyp_parser.add_argument("--make", default=None)
    hyp_parser.add_argument("--model", default=None)
    hyp_parser.add_argument("--engine", default=None)
    hyp_parser.add_argument("--complaint", default=None)
    hyp_parser.add_argument("--mileage", type=int, default=None)
    hyp_parser.add_argument("--compact", action="store_true", help="Print summary only")
    hyp_parser.set_defaults(func=cmd_hypothesis)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
