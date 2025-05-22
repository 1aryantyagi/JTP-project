import logging
import asyncpg
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

async def get_recommendations(product_name: str, pool, topn: int = 10) -> List[Dict[str, Any]]:
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
            
            return [dict(record) for record in results]
            
    except Exception as e:
        logger.error(f"Database error: {e}")
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