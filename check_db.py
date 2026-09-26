import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/antarctic_nav")
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT ST_AsGeoJSON(geometry::geometry) as geo, composite_risk
            FROM risk_cells
        """))
        features = []
        for row in res:
            features.append({
                "type": "Feature",
                "geometry": json.loads(row.geo),
                "properties": {"risk": row.composite_risk}
            })
        print(json.dumps({"type": "FeatureCollection", "features": features}, indent=2))

asyncio.run(main())
