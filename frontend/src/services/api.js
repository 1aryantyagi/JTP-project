// src/services/api.js
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const fetchRandomProducts = async () => {
    return axios.get(`${API_BASE}/random_products`);
};

export const fetchProductRecommendations = async (productId) => {
    return axios.get(`${API_BASE}/recommend/${encodeURIComponent(productId)}`);
};