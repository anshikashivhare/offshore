import asyncio
import json
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/antarctic_nav")
    
    ports_file = Path("backend/data/ports.json")
    if not ports_file.exists():
        print("backend/data/ports.json not found")
        return
        
    with open(ports_file, "r") as f:
        raw_ports = json.load(f)
        
    async with engine.begin() as conn:
        # Create table
        await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ports (
            port_id UUID PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            country VARCHAR(255),
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL
        )
        """))
        
        # Clear existing
        await conn.execute(text("TRUNCATE TABLE ports"))
        
        # Insert ports
        stmt = text("""
        INSERT INTO ports (port_id, name, country, latitude, longitude) 
        VALUES (:port_id, :name, :country, :latitude, :longitude)
        """)
        for p in raw_ports:
            lat = float(p.get("lat") if "lat" in p else p.get("latitude", 0.0))
            lon = float(p.get("lon") if "lon" in p else p.get("longitude", 0.0))
            # try to parse port_id as uuid, else generate one
            try:
                port_id = str(uuid.UUID(p.get("id")))
            except (ValueError, TypeError):
                port_id = str(uuid.uuid4())
                
            await conn.execute(stmt, {
                "port_id": port_id,
                "name": p.get("name", "Unknown"),
                "country": p.get("country", ""),
                "latitude": lat,
                "longitude": lon
            })
    
    print(f"Successfully seeded {len(raw_ports)} ports into the database.")

asyncio.run(main())
