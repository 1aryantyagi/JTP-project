import logging
import asyncpg
import os
from typing import List, Dict, Any
import random
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://db58_user:FWmXvvOVdAIyZYVlPTZ94kXWcImKLmrL@dpg-d0oh27emcj7s73d61sn0-a.singapore-postgres.render.com/db58"

async def get_recommendations(product_name: str, pool, topn: int = 15, sample_size: int = 7) -> List[Dict[str, Any]]:
    try:
        async with pool.acquire() as conn:
            target = await conn.fetchrow(
                "SELECT embedding FROM products WHERE product = $1",
                product_name
            )
            
            if not target:
                return []

            results = await conn.fetch(
                """
                SELECT product, category, sub_category, brand, sale_price, description
                FROM products
                WHERE product != $1
                ORDER BY embedding <=> $2
                LIMIT $3
                """,
                product_name, target['embedding'], topn
            )

            records = [dict(record) for record in results]
            
            return random.sample(records, min(sample_size, len(records)))

    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []

async def get_random_products(pool, n: int = 15) -> List[Dict[str, Any]]:
    try:
        async with pool.acquire() as conn:
            results = await conn.fetch(
                """
                SELECT product, category, sub_category, brand, sale_price, description
                FROM products
                ORDER BY RANDOM() LIMIT $1
                """,
                n
            )
            return [dict(record) for record in results]
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []