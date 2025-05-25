import asyncpg
import pandas as pd
from ast import literal_eval
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate_csv_to_db():
    """
    Asynchronously migrates product data from a CSV file into a PostgreSQL database.

    This function:
    - Connects to the PostgreSQL database using credentials from the `.env` file.
    - Loads product data from 'BigBasket_Products_emb.csv'.
    - Cleans missing values by filling nulls in string and numeric columns.
    - Parses stringified lists (e.g., embedding, category) using `literal_eval`.
    - Inserts each row into the `products` table, converting the embedding to pgvector format.

    CSV Columns expected:
        - product, category, sub_category, brand, sale_price, market_price,
          type, rating, description, embedding

    Notes:
        - The `embedding` column must be in a stringified list format (e.g., "[0.1, 0.2, ...]").
        - The `embedding` field is cast to `::vector` for pgvector compatibility.
        - The database URL is loaded from the `DATABASE_URL` variable in a `.env` file.

    Raises:
        asyncpg.PostgresError: If there is an issue during database connection or insertion.
    """
    
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    df = pd.read_csv('BigBasket_Products_emb.csv')

    df[['product', 'brand', 'description']] = df[['product', 'brand', 'description']].fillna('A')
    df[['sale_price', 'market_price', 'rating']] = df[['sale_price', 'market_price', 'rating']].fillna(0.0)

    df['embedding'] = df['embedding'].apply(literal_eval)
    df['category'] = df['category'].apply(literal_eval)
    df['sub_category'] = df['sub_category'].apply(literal_eval)
    df['type'] = df['type'].apply(literal_eval)

    for _, row in df.iterrows():
        embedding_str = f"[{', '.join(map(str, row['embedding']))}]"

        await conn.execute("""
            INSERT INTO products (
                product, category, sub_category, brand, sale_price,
                market_price, type, rating, description, embedding
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::vector)
        """,
            row['product'],
            row['category'],
            row['sub_category'],
            row['brand'],
            row['sale_price'],
            row['market_price'],
            row['type'],
            row['rating'],
            row['description'],
            embedding_str
        )


    await conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_csv_to_db())