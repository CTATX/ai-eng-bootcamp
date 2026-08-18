"""CLI for AutoZyte shop — status, ingest, hypothesis."""

from __future__ import annotations

import argparse
import json
import sys

from ferdai.hypothesis import build_hypothesis
from shop.ingest import (
    ensure_vehicle_for_vin,
    ingest_order_by_id,
    ingest_order_by_ticket,
    ingest_orders,
    ingest_status,
)
from shop.service import status as warehouse_status
from shop.synthetic import seed_if_empty
from shop.shopmonkey_client import ShopmonkeyAPIError, api_key_configured, auth_status


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


def cmd_ingest_ticket(args: argparse.Namespace) -> int:
    if not api_key_configured():
        print("SHOPMONKEY_API_KEY missing. Add it to .env.", file=sys.stderr)
        return 1
    try:
        result = ingest_order_by_ticket(
            args.ticket,
            pull_vehicle_history=not args.no_history,
        )
    except ShopmonkeyAPIError as exc:
        print(f"ShopMonkey error {exc.status_code}: {exc.message}", file=sys.stderr)
        return 1
    _print_json(result)
    return 0


def cmd_ingest_order(args: argparse.Namespace) -> int:
    if not api_key_configured():
        print("SHOPMONKEY_API_KEY missing. Add it to .env.", file=sys.stderr)
        return 1
    try:
        result = ingest_order_by_id(args.order_id)
    except ShopmonkeyAPIError as exc:
        print(f"ShopMonkey error {exc.status_code}: {exc.message}", file=sys.stderr)
        return 1
    _print_json(result)
    return 0


def cmd_hypothesis(args: argparse.Namespace) -> int:
    seed_if_empty()
    if args.vin and api_key_configured():
        ensure_vehicle_for_vin(args.vin.strip())
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
        description="AutoZyte shop CLI — synthetic warehouse now, ShopMonkey when keyed."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    status_parser = sub.add_parser("status", help="Warehouse + ingest + key status")
    status_parser.set_defaults(func=cmd_status)

    ingest_parser = sub.add_parser("ingest", help="Pull ShopMonkey orders into warehouse")
    ingest_parser.add_argument("--page-size", type=int, default=25)
    ingest_parser.add_argument("--max-pages", type=int, default=None)
    ingest_parser.set_defaults(func=cmd_ingest)

    ticket_parser = sub.add_parser(
        "ingest-ticket",
        help="Pull one ShopMonkey RO by ticket number (then that vehicle's history)",
    )
    ticket_parser.add_argument("ticket", help="RO / ticket number from ShopMonkey (e.g. 1042)")
    ticket_parser.add_argument(
        "--no-history",
        action="store_true",
        help="Only ingest this ticket, not other orders for the same vehicle",
    )
    ticket_parser.set_defaults(func=cmd_ingest_ticket)

    order_parser = sub.add_parser("ingest-order", help="Pull one ShopMonkey order by API id (UUID)")
    order_parser.add_argument("order_id", help="ShopMonkey order id")
    order_parser.set_defaults(func=cmd_ingest_order)

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
