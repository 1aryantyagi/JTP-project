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
    """
    Retrieve product recommendations based on vector similarity.

    This function fetches the embedding of the given product and retrieves the top-N
    most similar products using vector similarity (<=>) from a PostgreSQL database.
    From these, it returns a random sample of results for variety.

    Args:
        product_name (str): The name of the product for which recommendations are needed.
        pool: The asyncpg database connection pool.
        topn (int, optional): Number of top similar products to consider. Default is 12.
        sample_size (int, optional): Number of products to return from the top results. Default is 7.

    Returns:
        List[Dict[str, Any]]: A list of recommended products as dictionaries. Returns
        an empty list if the target product is not found or an error occurs.
    """
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

    """
    Fetch a random sample of products from the database.

    This function queries the `products` table to retrieve a random selection of
    product entries, limited by the specified number.

    Args:
        pool: The asyncpg database connection pool.
        n (int, optional): Number of random products to retrieve. Default is 15.

    Returns:
        List[Dict[str, Any]]: A list of product records as dictionaries. 
        Returns an empty list if a database error occurs.
    """

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

    """
    Generate product recommendations based on a list of products in the user's cart.

    For each product in the cart, this function retrieves its embedding and fetches the top-N
    similar products using vector similarity. It then aggregates and ranks the most frequently
    recommended items across all input products, excluding those already in the cart.
    
        - Uses the pgvector `<=>` operator for embedding similarity.
        - Each product in the cart contributes its own top-N similar products.
        - Duplicate recommendations are merged and ranked by frequency.
        - Products already present in the cart are excluded from the result.

    Args:
        product_names (List[str]): List of product names currently in the user's cart.
        pool: The asyncpg database connection pool.
        topn (int, optional): Number of final recommended products to return. Default is 12.

    Returns:
        List[Dict[str, Any]]: A list of recommended product dictionaries, ranked by relevance.
        Returns an empty list if no recommendations can be made or if an error occurs.
    """

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