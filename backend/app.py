# app.py
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import unquote
import logging

from main import get_recommendations, get_random_products

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define response models with complete product details
class Product(BaseModel):
    product: str
    category: List[str]
    sub_category: List[str]
    brand: str
    sale_price: float
    description: Optional[str] = None
    type: List[str]
    # Add other fields as needed from your dataset

class RecommendationsResponse(BaseModel):
    recommendations: List[Product]

class RandomProductsResponse(BaseModel):
    products: List[Product]

@app.get("/", tags=["Root"])
async def root():
    """Health check endpoint"""
    return {"message": "Product Recommendation API is running."}

@app.get("/random_products", response_model=RandomProductsResponse, tags=["Products"])
async def get_random_products_endpoint():
    """
    Retrieve a list of random products with full details
    """
    try:
        products = get_random_products()
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
    Get product recommendations with full details based on the given product name
    """
    decoded_name = unquote(product_name)
    try:
        recommendations = get_recommendations(decoded_name)
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