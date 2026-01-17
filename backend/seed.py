#!/usr/bin/env python3
"""
M-SUITE Database Seed Script
Creates initial demo account and sample vehicles.
"""

import asyncio
import bcrypt
from src.database import engine, async_session_maker, Base
from src.auth.models import Owner
from src.vehicles.models import Vehicle, VehicleMode, InteriorMode
from src.earnings.models import Earning  # Required for relationship


def hash_password(password: str) -> str:
    """Hash password using bcrypt directly."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


async def seed_database():
    """Create initial data for development/demo purposes."""

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as db:
        # Check if demo account already exists
        from sqlalchemy import select
        result = await db.execute(select(Owner).where(Owner.email == "admin@sample.com"))
        existing = result.scalar_one_or_none()

        if existing:
            print("Demo account already exists. Skipping seed.")
            return

        # Create demo owner
        owner = Owner(
            email="admin@sample.com",
            hashed_password=hash_password("password123"),
            full_name="Admin User",
            phone="090-1234-5678",
            is_active=True,
        )
        db.add(owner)
        await db.commit()
        await db.refresh(owner)
        print(f"Created demo owner: {owner.email}")

        # Create sample vehicles
        vehicles_data = [
            {
                "name": "Tesla Model 3",
                "license_plate": "品川 500 あ 1234",
                "model": "Model 3 Long Range",
                "year": 2023,
                "current_mode": VehicleMode.IDLE,
                "interior_mode": InteriorMode.STANDARD,
                "battery_level": 85.0,
                "latitude": 35.6762,
                "longitude": 139.6503,
                "allowed_modes": ["accommodation", "delivery", "rideshare"],
            },
            {
                "name": "Toyota Alphard",
                "license_plate": "横浜 300 さ 5678",
                "model": "Alphard Hybrid",
                "year": 2022,
                "current_mode": VehicleMode.ACCOMMODATION,
                "interior_mode": InteriorMode.BED,
                "battery_level": 100.0,
                "current_hourly_rate": 5000,
                "latitude": 35.4437,
                "longitude": 139.6380,
                "allowed_modes": ["accommodation", "rideshare"],
            },
        ]

        for v_data in vehicles_data:
            vehicle = Vehicle(owner_id=owner.id, **v_data)
            db.add(vehicle)
            print(f"Created vehicle: {v_data['name']}")

        await db.commit()
        print("\nSeed completed successfully!")
        print("=" * 40)
        print("Demo Account:")
        print("  Email:    admin@sample.com")
        print("  Password: password123")
        print("=" * 40)


if __name__ == "__main__":
    asyncio.run(seed_database())
