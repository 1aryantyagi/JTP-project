from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import unquote
from main import get_recommendations, get_random_products
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/bigbasket_local"

pool = None

async def get_db_pool():
    global pool
    if pool is None:
        retries = 5
        delay = 2
        for attempt in range(retries):
            try:
                logger.info(f"Attempt {attempt+1}/{retries}: Creating database connection pool...")
                pool = await asyncpg.create_pool(
                    dsn=DATABASE_URL,
                    min_size=5,
                    max_size=20,
                    timeout=30
                )
                await test_connection(pool)
                logger.info("Successfully created database connection pool")
                return pool
            except Exception as e:
                logger.warning(f"Connection attempt {attempt+1} failed: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(delay * (attempt + 1))
                    continue
                raise
    return pool

async def test_connection(pool):
    async with pool.acquire() as connection:
        await connection.execute("SELECT 1")

class Product(BaseModel):
    product: str
    category: List[str]
    sub_category: List[str]
    brand: str
    sale_price: float
    description: Optional[str] = None
    type: Optional[List[str]] = None

class RecommendationsResponse(BaseModel):
    recommendations: List[Product]

class RandomProductsResponse(BaseModel):
    products: List[Product]

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Product Recommendation API is running."}

@app.get("/random_products", response_model=RandomProductsResponse, tags=["Products"])
async def get_random_products_endpoint():
    logger.info("Request received for random products")
    try:
        pool = await get_db_pool()
        products = await get_random_products(pool)
        return {"products": products}
    except Exception as e:
        logger.error(f"Error fetching random products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

@app.get("/recommend/{product_name}", response_model=RecommendationsResponse, tags=["Recommendations"])
async def get_recommendations_endpoint(product_name: str):
    logger.info(f"Request received for recommendations of: {product_name}")
    decoded_name = unquote(product_name)
    try:
        pool = await get_db_pool()
        recommendations = await get_recommendations(decoded_name, pool)
        if not recommendations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No recommendations found for '{decoded_name}'"
            )
        return {"recommendations": recommendations}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recommendations for {decoded_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

@app.on_event("startup")
async def startup():
    await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()