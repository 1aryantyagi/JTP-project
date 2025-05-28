import axios from 'axios';

// Determine API base URL based on environment
const isProduction = process.env.NODE_ENV === 'production';
const API_BASE = isProduction
    ? '/api'
    : 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE,
});

api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => {
    return Promise.reject(error);
});

api.interceptors.response.use(response => {
    return response;
}, error => {
    if (error.response && error.response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    }
    return Promise.reject(error);
});

export const fetchRandomProducts = async () => {
    return api.get('/random_products');
};

export const fetchProductRecommendations = async (productId) => {
    return api.get(`/recommend/${encodeURIComponent(productId)}`);
};

export const fetchCartRecommendations = (productNames) => {
    return api.post('/recommend/cart', { product_names: productNames });
};

export const loginUser = async (credentials) => {
    return api.post('/login', credentials, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    });
};

export const registerUser = async (userData) => {
    return api.post('/register', userData);
};