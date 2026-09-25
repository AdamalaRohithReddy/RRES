"""Database Management CLI for Milestone 7.

Provides administrative commands to check connection health, initialize schemas,
seed demo records, and inspect stored entities.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys

from src.database.connection import check_connection_health, init_db, drop_db, get_engine
from src.database.seed import seed_database
from src.database.repositories.citizen_repo import CitizenRepository
from src.database.repositories.application_repo import ApplicationRepository

logger = logging.getLogger(__name__)


def cmd_health(args):
    """Run database connectivity health check."""
    result = check_connection_health()
    print("Database Connection Status:")
    print(f"  URL:     {result['url']}")
    print(f"  Healthy: {'YES' if result['healthy'] else 'NO'}")
    if result["latency_ms"] is not None:
        print(f"  Latency: {result['latency_ms']} ms")
    if result["error"]:
        print(f"  Error:   {result['error']}")
    if not result["healthy"]:
        sys.exit(1)


def cmd_init(args):
    """Initialize database tables."""
    print("Initializing database tables...")
    init_db()
    print("Tables created successfully.")


def cmd_seed(args):
    """Seed database with demo citizen and application records."""
    print("Seeding database with DEMO records...")
    seed_database(force_refresh=args.force)
    print("Seeding completed successfully.")


def cmd_inspect(args):
    """Inspect stored citizens or applications."""
    citizen_repo = CitizenRepository()
    app_repo = ApplicationRepository()

    if args.type == "citizens":
        citizens = citizen_repo.list_citizens()
        print(f"\n--- Stored Citizens ({len(citizens)}) ---")
        for c in citizens:
            print(f"[{c['citizen_id']}] {c['name']} (Age: {c.get('age', 'N/A')}, State: {c.get('state', 'N/A')})")
    elif args.type == "applications":
        print("\n--- Demonstration Applications ---")
        for aid in ["DEMO-001", "DEMO-002", "DEMO-003"]:
            app = app_repo.get_application(aid)
            if app:
                print(f"[{app['application_id']}] {app['scheme_name']} -> {app['status']}")
            else:
                print(f"[{aid}] Not found.")


def main():
    parser = argparse.ArgumentParser(description="Citizen AI Database Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # health
    subparsers.add_parser("health", help="Check database connection health")

    # init
    subparsers.add_parser("init", help="Create database tables")

    # seed
    seed_p = subparsers.add_parser("seed", help="Seed database with demo data")
    seed_p.add_argument("--force", action="store_true", help="Force overwrite existing records")

    # inspect
    inspect_p = subparsers.add_parser("inspect", help="Inspect stored records")
    inspect_p.add_argument("type", choices=["citizens", "applications"], default="citizens")

    args = parser.parse_args()

    if args.command == "health":
        cmd_health(args)
    elif args.command == "init":
        cmd_init(args)
    elif args.command == "seed":
        cmd_seed(args)
    elif args.command == "inspect":
        cmd_inspect(args)


if __name__ == "__main__":
    main()
