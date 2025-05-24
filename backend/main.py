import logging
import asyncpg
import os
from collections import Counter
from typing import List, Dict, Any
import random
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/bigbasket_local"

async def get_recommendations(product_name: str, pool, topn: int = 12, sample_size: int = 7) -> List[Dict[str, Any]]:
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

async def get_cart_recommendations(product_names: List[str], pool, topn: int = 12) -> List[Dict[str, Any]]:
    try:
        async with pool.acquire() as conn:
            topn_per_product = 8
            all_recommendations = []
            seen_products = set(product_names)

            for product_name in product_names:
                record = await conn.fetchrow(
                    "SELECT embedding FROM products WHERE product = $1",
                    product_name
                )
                if not record or not record['embedding']:
                    continue

                embedding = record['embedding']

                results = await conn.fetch(
                    """
                    SELECT product, category, sub_category, brand, sale_price, description
                    FROM products
                    WHERE product != $1
                    ORDER BY embedding <=> $2
                    LIMIT $3
                    """,
                    product_name,
                    embedding,
                    topn_per_product
                )
                all_recommendations.extend([dict(r) for r in results if r['product'] not in seen_products])

            freq_counter = Counter([r['product'] for r in all_recommendations])

            ranked = sorted(
                {r['product']: r for r in all_recommendations}.values(),
                key=lambda x: freq_counter[x['product']],
                reverse=True
            )

            return ranked[:topn]

    except Exception as e:
        logger.error(f"Error getting cart recommendations: {e}")
        return []