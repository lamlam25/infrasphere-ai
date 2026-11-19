import asyncio
import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import create_tables, AsyncSessionLocal
from app.seed.demo_data import seed_all_data

async def main():
    print("Testing table creation...")
    await create_tables()
    print("TABLES_CREATED_OK")
    print("Testing data seed...")
    async with AsyncSessionLocal() as session:
        await seed_all_data(session)
    print("DATA_SEEDED_OK")

if __name__ == "__main__":
    asyncio.run(main())
