"""Database seed utility for Milestone 7.

Seeds the database with controlled demonstration citizens and application records.
All seeded records are clearly identified as DEMO / TEST DATA.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.engine import Engine

from src.database.connection import get_db_session, init_db
from src.database.repositories.citizen_repo import CitizenRepository
from src.database.repositories.application_repo import ApplicationRepository

logger = logging.getLogger(__name__)

# Predefined demonstration citizen profiles
DEMO_CITIZENS = [
    {
        "citizen_id": "demo-user",
        "name": "Ramesh Kumar",
        "date_of_birth": date(1998, 5, 15),
        "gender": "Male",
        "phone": "+91-9876543210",
        "profile": {
            "state": "Telangana",
            "district": "Hyderabad",
            "annual_income": Decimal("240000.00"),
            "occupation": "Tech Startup Founder",
            "has_dpiit_recognition": True,
            "business_incorporated_years": 1,
            "category": "General",
            "is_taxpayer": False,
            "is_differently_abled": False,
        },
    },
    {
        "citizen_id": "senior-citizen",
        "name": "Lakshmi Devi",
        "date_of_birth": date(1961, 8, 20),
        "gender": "Female",
        "phone": "+91-9876543211",
        "profile": {
            "state": "Telangana",
            "district": "Warangal",
            "annual_income": Decimal("150000.00"),
            "occupation": "Retired / Domestic Worker",
            "has_dpiit_recognition": False,
            "category": "General",
            "is_taxpayer": False,
            "is_differently_abled": False,
        },
    },
    {
        "citizen_id": "rural-farmer",
        "name": "Suresh Patel",
        "date_of_birth": date(1984, 3, 10),
        "gender": "Male",
        "phone": "+91-9876543212",
        "profile": {
            "state": "Gujarat",
            "district": "Anand",
            "annual_income": Decimal("180000.00"),
            "occupation": "Smallholder Farmer",
            "has_dpiit_recognition": False,
            "category": "OBC",
            "is_taxpayer": False,
            "landholding_acres": Decimal("2.50"),
            "is_differently_abled": False,
        },
    },
]

# Predefined demonstration application tracking records
DEMO_APPLICATIONS = [
    {
        "application_id": "DEMO-001",
        "citizen_id": "demo-user",
        "scheme_name": "Startup India Seed Fund Scheme",
        "status": "Under Evaluation by Incubator Seed Management Committee (ISMC)",
        "submitted_date": date(2026, 8, 15),
        "incubator_preference": "T-Hub Hyderabad",
        "milestone_stage": "Proof of Concept Validation",
        "next_step": "Awaiting final interview schedule notification by email.",
    },
    {
        "application_id": "DEMO-002",
        "citizen_id": "senior-citizen",
        "scheme_name": "Atal Pension Yojana",
        "status": "Active / Enrolled",
        "submitted_date": date(2025, 11, 10),
        "pran_status": "Generated",
        "next_step": "Maintain sufficient balance for monthly auto-debit on 1st of month.",
    },
    {
        "application_id": "DEMO-003",
        "citizen_id": "demo-user",
        "scheme_name": "Startup India Seed Fund Scheme",
        "status": "Rejected by Incubator Preference 1; Forwarded to Incubator Preference 2",
        "submitted_date": date(2026, 7, 20),
        "next_step": "Under review by secondary incubator ISMC.",
    },
]


def seed_database(engine: Optional[Engine] = None, force_refresh: bool = False) -> None:
    """Populate database with controlled demonstration citizens and applications.
    
    Creates tables if they do not exist. Idempotently inserts or updates demo records.
    """
    init_db(engine=engine)

    with get_db_session(engine=engine) as session:
        citizen_repo = CitizenRepository(session=session)
        app_repo = ApplicationRepository(session=session)

        # 1. Seed Citizens and Profiles
        for c_data in DEMO_CITIZENS:
            cid = c_data["citizen_id"]
            existing = citizen_repo.get_citizen(cid)
            if existing and not force_refresh:
                logger.info(f"Demo citizen '{cid}' already exists, skipping.")
                continue

            citizen_repo.create_or_update_citizen(
                citizen_id=cid,
                name=c_data["name"],
                date_of_birth=c_data["date_of_birth"],
                gender=c_data["gender"],
                phone=c_data["phone"],
            )

            prof = c_data["profile"]
            citizen_repo.create_or_update_profile(
                citizen_id=cid,
                state=prof.get("state"),
                district=prof.get("district"),
                annual_income=prof.get("annual_income"),
                occupation=prof.get("occupation"),
                category=prof.get("category"),
                is_taxpayer=prof.get("is_taxpayer", False),
                has_dpiit_recognition=prof.get("has_dpiit_recognition", False),
                business_incorporated_years=prof.get("business_incorporated_years"),
                landholding_acres=prof.get("landholding_acres"),
                is_differently_abled=prof.get("is_differently_abled", False),
            )
            logger.info(f"Seeded demo citizen and profile for '{cid}'.")

        # 2. Seed Applications
        for a_data in DEMO_APPLICATIONS:
            aid = a_data["application_id"]
            existing_app = app_repo.get_application(aid)
            if existing_app and not force_refresh:
                logger.info(f"Demo application '{aid}' already exists, skipping.")
                continue

            app_repo.create_application(
                application_id=aid,
                citizen_id=a_data["citizen_id"],
                scheme_name=a_data["scheme_name"],
                status=a_data["status"],
                submitted_date=a_data["submitted_date"],
                incubator_preference=a_data.get("incubator_preference"),
                milestone_stage=a_data.get("milestone_stage"),
                pran_status=a_data.get("pran_status"),
                next_step=a_data.get("next_step"),
            )
            logger.info(f"Seeded demo application '{aid}'.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Seeding database with DEMO data...")
    seed_database()
    print("Database seeding completed.")
