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

# Create main FastAPI app
app = FastAPI()

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create API router for all endpoints under /api
api_router = APIRouter()

# Security setup with updated token URL
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

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

# Pydantic models
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

# Root endpoint (not under /api)
@app.get("/", tags=["Root"])
async def root():
    return {"message": "Product Recommendation API is running."}

# API endpoints (mounted under /api)
@api_router.get("/random_products", response_model=RandomProductsResponse, tags=["Products"])
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

@api_router.get("/recommend/{product_name}", response_model=RecommendationsResponse, tags=["Recommendations"])
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

@api_router.post("/recommend/cart", response_model=RecommendationsResponse, tags=["Recommendations"])
async def get_cart_recommendations_endpoint(request: CartRecommendationRequest):
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

# Mount the API router under /api prefix
app.include_router(api_router, prefix="/api")

# Startup/shutdown events
@app.on_event("startup")
async def startup():
    await get_db_pool()

@app.on_event("shutdown")
async def shutdown():
    if pool:
        await pool.close()