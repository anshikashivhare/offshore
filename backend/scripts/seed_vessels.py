import asyncio
import json
import os
import sys

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.session import AsyncSessionLocal, engine
from app.models.base import Base
from app.models.vessel import Vessel
from app.models import __all__ as _models
from sqlalchemy import select


async def seed_vessels():
    print("Creating/updating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Seeding vessels from JSON...")
    json_path = os.path.join(os.path.dirname(__file__), "..", "data", "vessels.json")
    
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, "r") as f:
        vessels_data = json.load(f)

    async with AsyncSessionLocal() as session:
        for v_data in vessels_data:
            # Check if exists
            result = await session.execute(
                select(Vessel).filter_by(vessel_id=v_data["vessel_id"])
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"Updating vessel: {v_data['vessel_name']}")
                for key, value in v_data.items():
                    setattr(existing, key, value)
            else:
                print(f"Inserting vessel: {v_data['vessel_name']}")
                new_vessel = Vessel(**v_data)
                session.add(new_vessel)
        
        await session.commit()
    print("Vessel seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_vessels())
