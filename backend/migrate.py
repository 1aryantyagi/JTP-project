import asyncpg
import pandas as pd
from ast import literal_eval
import os
from dotenv import load_dotenv

load_dotenv()

async def migrate_csv_to_db():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    df = pd.read_csv('BigBasket_Products_emb.csv')

    df[['product', 'brand', 'description', 'soup']] = df[['product', 'brand', 'description', 'soup']].fillna('A')
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
                market_price, type, rating, description, soup, embedding
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::vector)
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
            row['soup'],
            embedding_str
        )


    await conn.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(migrate_csv_to_db())