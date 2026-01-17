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

        # Create sample vehicles around Tokyo Station (35.6812, 139.7671)
        vehicles_data = [
            # 東京駅 丸の内側
            {
                "name": "Tesla Model S #001",
                "license_plate": "品川 500 あ 1001",
                "model": "Model S",
                "year": 2024,
                "current_mode": VehicleMode.IDLE,
                "interior_mode": InteriorMode.STANDARD,
                "battery_level": 92.0,
                "latitude": 35.6814,
                "longitude": 139.7670,
                "allowed_modes": ["accommodation", "delivery", "rideshare"],
                "current_hourly_rate": 0,
                "today_earnings": 0,
            },
            # 東京駅 八重洲側
            {
                "name": "Tesla Model 3 #002",
                "license_plate": "品川 500 い 1002",
                "model": "Model 3",
                "year": 2023,
                "current_mode": VehicleMode.ACCOMMODATION,
                "interior_mode": InteriorMode.BED,
                "battery_level": 78.0,
                "current_hourly_rate": 4500,
                "today_earnings": 13500,
                "latitude": 35.6805,
                "longitude": 139.7690,
                "allowed_modes": ["accommodation", "delivery", "rideshare"],
            },
            # 日本橋エリア
            {
                "name": "Tesla Model X #003",
                "license_plate": "品川 300 う 1003",
                "model": "Model X",
                "year": 2024,
                "current_mode": VehicleMode.DELIVERY,
                "interior_mode": InteriorMode.CARGO,
                "battery_level": 65.0,
                "current_hourly_rate": 3200,
                "today_earnings": 9600,
                "latitude": 35.6839,
                "longitude": 139.7744,
                "allowed_modes": ["accommodation", "delivery", "rideshare"],
            },
            # 銀座エリア
            {
                "name": "Tesla Model Y #004",
                "license_plate": "品川 500 え 1004",
                "model": "Model Y",
                "year": 2023,
                "current_mode": VehicleMode.RIDESHARE,
                "interior_mode": InteriorMode.PASSENGER,
                "battery_level": 54.0,
                "current_hourly_rate": 2800,
                "today_earnings": 16800,
                "latitude": 35.6717,
                "longitude": 139.7649,
                "allowed_modes": ["accommodation", "delivery", "rideshare"],
            },
            # 有楽町エリア
            {
                "name": "Tesla Model 3 #005",
                "license_plate": "品川 500 お 1005",
                "model": "Model 3",
                "year": 2022,
                "current_mode": VehicleMode.CHARGING,
                "interior_mode": InteriorMode.STANDARD,
                "battery_level": 23.0,
                "current_hourly_rate": 0,
                "today_earnings": 8400,
                "latitude": 35.6750,
                "longitude": 139.7630,
                "allowed_modes": ["accommodation", "delivery", "rideshare"],
            },
            # 京橋エリア
            {
                "name": "Tesla Model S #006",
                "license_plate": "品川 500 か 1006",
                "model": "Model S",
                "year": 2024,
                "current_mode": VehicleMode.ACCOMMODATION,
                "interior_mode": InteriorMode.BED,
                "battery_level": 88.0,
                "current_hourly_rate": 5500,
                "today_earnings": 22000,
                "latitude": 35.6773,
                "longitude": 139.7712,
                "allowed_modes": ["accommodation", "rideshare"],
            },
            # 大手町エリア
            {
                "name": "Tesla Model Y #007",
                "license_plate": "品川 300 き 1007",
                "model": "Model Y",
                "year": 2023,
                "current_mode": VehicleMode.IDLE,
                "interior_mode": InteriorMode.STANDARD,
                "battery_level": 100.0,
                "current_hourly_rate": 0,
                "today_earnings": 0,
                "latitude": 35.6867,
                "longitude": 139.7639,
                "allowed_modes": ["delivery", "rideshare"],
            },
            # 神田エリア
            {
                "name": "Tesla Model X #008",
                "license_plate": "品川 300 く 1008",
                "model": "Model X",
                "year": 2022,
                "current_mode": VehicleMode.MAINTENANCE,
                "interior_mode": InteriorMode.STANDARD,
                "battery_level": 45.0,
                "current_hourly_rate": 0,
                "today_earnings": 5600,
                "latitude": 35.6918,
                "longitude": 139.7710,
                "allowed_modes": ["accommodation", "delivery", "rideshare"],
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
