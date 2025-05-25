from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import unquote
from main import get_recommendations, get_random_products, get_cart_recommendations
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
    """
    Create and return a global asyncpg database connection pool.

    This function attempts to create a global database connection pool using
    `asyncpg.create_pool`. It will retry the connection up to 5 times with an 
    exponential backoff delay if a failure occurs.

    - Uses global `pool` variable to ensure only one pool is created.
    - Logs each connection attempt and success or failure.
    - Calls `test_connection(pool)` to verify the connection before returning.

    Returns:
        asyncpg.pool.Pool: The database connection pool.

    Raises:
        Exception: If all retry attempts to create the pool fail.
    """
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

class CartRecommendationRequest(BaseModel):
    product_names: List[str]

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Product Recommendation API is running."}

@app.get("/random_products", response_model=RandomProductsResponse, tags=["Products"])
async def get_random_products_endpoint():

    """
    Handles GET requests to fetch a list of random products.

    - Connects to the database using a connection pool.
    - Retrieves random product entries.
    - Returns them in the format defined by RandomProductsResponse.
    - Logs request and errors.
    - Returns a 500 error if something goes wrong during the process.
    """

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

    """
    Handles GET requests to fetch product recommendations based on a given product name.

    - Decodes the product name from the URL.
    - Connects to the database using a connection pool.
    - Retrieves a list of recommended products using the provided name.
    - Returns a 404 error if no recommendations are found.
    - Returns a 500 error if an unexpected error occurs.
    - Logs the request and any exceptions encountered.
    
    Args:
        product_name (str): The name of the product for which recommendations are requested.

    Returns:
        dict: A dictionary with a "recommendations" key containing the list of recommended products.
    """

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

@app.post("/recommend/cart", response_model=RecommendationsResponse, tags=["Recommendations"])
async def get_cart_recommendations_endpoint(request: CartRecommendationRequest):

    """
    Handles POST requests to fetch product recommendations based on the contents of a shopping cart.

    - Accepts a list of product names in the request body.
    - Connects to the database using a connection pool.
    - Retrieves a list of recommended products based on the provided cart items.
    - Returns the recommendations in the format defined by RecommendationsResponse.
    - Logs the request and any exceptions that occur.
    - Returns a 500 error if an unexpected error is encountered.

    Args:
        request (CartRecommendationRequest): Request body containing a list of product names.

    Returns:
        dict: A dictionary with a "recommendations" key containing the list of recommended products.
    """

    logger.info(f"Request received for cart recommendations")
    try:
        pool = await get_db_pool()
        recommendations = await get_cart_recommendations(request.product_names, pool)
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Error fetching cart recommendations: {e}")
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