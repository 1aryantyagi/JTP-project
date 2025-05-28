from fastapi import FastAPI, HTTPException, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import unquote
from main import get_recommendations, get_random_products, get_cart_recommendations
import asyncio
import asyncpg
import os
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import base64
import json
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

api_router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/bigbasket_local"

pool = None

async def get_db_pool():

    """
    Creates and returns a global asyncpg connection pool to the PostgreSQL database.

    This function checks if a global `pool` is already initialized. If not, it attempts to create 
    a new asyncpg connection pool with retry logic. The pool is tested with a sample query to ensure 
    it's operational. If all retry attempts fail, the exception is raised.

    Returns:
        asyncpg.pool.Pool: The initialized database connection pool.

    Raises:
        Exception: If all attempts to create the pool fail.
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

class UserBase(BaseModel):
    name: str
    user_id: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

class Token(BaseModel):
    access_token: str
    token_type: str

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Product Recommendation API is running."}

@api_router.get("/random_products", response_model=RandomProductsResponse, tags=["Products"])
async def get_random_products_endpoint():

    """
    GET endpoint to retrieve a list of random products from the database.

    This endpoint logs the request, establishes a connection to the database 
    using the connection pool, and fetches random product entries using 
    the `get_random_products` function.

    Returns:
        dict: A dictionary with a `products` key containing a list of random product data.

    Raises:
        HTTPException: Returns a 500 Internal Server Error if database connection or 
                       product retrieval fails.
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

@api_router.get("/recommend/{product_name}", response_model=RecommendationsResponse, tags=["Recommendations"])
async def get_recommendations_endpoint(product_name: str):

    """
    GET endpoint to retrieve product recommendations based on a given product name.

    This endpoint decodes the provided product name, retrieves a database connection 
    pool, and fetches a list of recommended products using the `get_recommendations` function.

    Args:
        product_name (str): The name of the product to get recommendations for (URL-encoded).

    Returns:
        dict: A dictionary with a `recommendations` key containing a list of recommended products.

    Raises:
        HTTPException: 
            - 404 Not Found if no recommendations are found for the given product.
            - 500 Internal Server Error if an unexpected error occurs.
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

@api_router.post("/recommend/cart", response_model=RecommendationsResponse, tags=["Recommendations"])
async def get_cart_recommendations_endpoint(request: CartRecommendationRequest):

    """
    POST endpoint to retrieve product recommendations based on multiple items in a user's cart.

    This endpoint receives a list of product names from the request body, retrieves a database 
    connection pool, and returns recommendations using the `get_cart_recommendations` function.

    Args:
        request (CartRecommendationRequest): The request body containing a list of product names.

    Returns:
        dict: A dictionary with a `recommendations` key containing a list of recommended products.

    Raises:
        HTTPException: Returns a 500 Internal Server Error if recommendation fetching fails.
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

@api_router.post("/register", response_model=User, tags=["Authentication"])
async def register_user(user: UserCreate):

    """
    POST endpoint to register a new user.

    This endpoint checks if the provided user ID already exists in the database. 
    If it does not exist, it hashes the password and inserts the new user's 
    information into the database.

    Args:
        user (UserCreate): The user registration data including name, user ID, and plain-text password.

    Returns:
        dict: A dictionary containing the newly created user's ID, name, and user ID.

    Raises:
        HTTPException:
            - 400: If the user ID already exists in the database.
            - 500: If an internal server error occurs during registration.
    """
    logger.info(f"Request received for user registration")
    try:
        pool = await get_db_pool()
        async with pool.acquire() as connection:
            exists = await connection.fetchval(
                "SELECT 1 FROM users WHERE user_id = $1", user.user_id
            )
            if exists:
                raise HTTPException(
                    status_code=400,
                    detail="User ID already exists"
                )
            
            hashed_password = pwd_context.hash(user.password)
            
            new_user = await connection.fetchrow(
                "INSERT INTO users (name, user_id, password) VALUES ($1, $2, $3) RETURNING id, name, user_id",
                user.name, user.user_id, hashed_password
            )
            return dict(new_user)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

@api_router.post("/login", response_model=Token, tags=["Authentication"])
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):

    """
    POST endpoint to authenticate a user and return an access token.

    This endpoint verifies the provided user ID and password against stored credentials.
    If valid, it encodes user data into a base64 token and returns it as a bearer token.

    Args:
        form_data (OAuth2PasswordRequestForm): The login form data containing `username` (user_id)
                                               and `password`, passed via dependency injection.

    Returns:
        dict: A dictionary with the access token and its type (`bearer`).

    Raises:
        HTTPException:
            - 401: If credentials are invalid (user not found or incorrect password).
            - 500: If an internal server error occurs during the login process.
    """
    logger.info(f"Request received for user login")
    try:
        pool = await get_db_pool()
        async with pool.acquire() as connection:
            user = await connection.fetchrow(
                "SELECT * FROM users WHERE user_id = $1", 
                form_data.username
            )
            
            if not user or not pwd_context.verify(form_data.password, user["password"]):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token_data = {
                "sub": user["user_id"],
                "name": user["name"]
            }
            token = base64.b64encode(json.dumps(token_data).encode()).decode()
            
            return {"access_token": token, "token_type": "bearer"}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup():
    await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()