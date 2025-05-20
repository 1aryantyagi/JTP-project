import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from urllib.parse import unquote
import ast

df = pd.read_csv('BigBasket_Products_emb.csv')

df['embedding'] = df['embedding'].apply(ast.literal_eval)

embeddings = np.array(df['embedding'].to_list())

cosine_sim = cosine_similarity(embeddings, embeddings)

df = df.reset_index(drop=True)
indices = pd.Series(df.index, index=df['product']).drop_duplicates()

def parse_list_fields(row, list_fields):
    for field in list_fields:
        if isinstance(row[field], str) and row[field].startswith("["):
            try:
                row[field] = ast.literal_eval(row[field])
            except:
                row[field] = []
    return row
    
def get_recommendations(product_name, topn=10):
    try:
        decoded = unquote(product_name)
        logger.info(f"Getting recommendations for: {decoded}")
        idx = indices[decoded]
        if isinstance(idx, pd.Series):
            idx = idx.iloc[0]
    except KeyError:
        logger.warning(f"Product not found: {product_name}")
        return None

    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1: topn+1]
    rec_idxs = [i for i, _ in sim_scores]

    exclude_keys = {'embedding', 'rating', 'soup', 'index'}
    list_fields = ['category', 'sub_category', 'type']

    recommendations = []
    for _, row in df.iloc[rec_idxs].copy().iterrows():
        row = parse_list_fields(row, list_fields)
        filtered = {k: v for k, v in row.items() if k not in exclude_keys}
        recommendations.append(filtered)

    logger.info(f"Found {len(recommendations)} recommendations for {decoded}")
    return recommendations

def get_random_products(n=15):
    logger.info(f"Fetching {n} random products")
    sample_df = df.sample(n=n).copy()
    list_fields = ['category', 'sub_category', 'type']
    sample_df = sample_df.apply(lambda row: parse_list_fields(row, list_fields), axis=1)
    logger.info("Random products fetched successfully")
    return sample_df.to_dict('records')