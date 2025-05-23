// src/pages/Dashboard.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProductCard from '../components/ProductCard';
import { fetchRandomProducts } from '../services/api';
import './Dashboard.css';

const Dashboard = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sortOrder, setSortOrder] = useState('default');
    const navigate = useNavigate();

    const loadProducts = async () => {
        try {
            setLoading(true);
            const response = await fetchRandomProducts();
            setProducts(response.data.products);
        } catch (error) {
            console.error('Error loading products:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadProducts();
    }, []);

    const handleSortChange = (e) => {
        const order = e.target.value;
        setSortOrder(order);

        // Clone the array before sorting
        const sortedProducts = [...products].sort((a, b) => {
            const priceA = parseFloat(a.sale_price);
            const priceB = parseFloat(b.sale_price);

            if (order === 'lowToHigh') return priceA - priceB;
            if (order === 'highToLow') return priceB - priceA;
            return 0;
        });

        setProducts(sortedProducts);
    };

    const handleProductSelect = (productId) => {
        navigate(`/recommendations/${productId}`);
    };

    return (
        <div className="dashboard">
            <div className="dashboard-header">
                <h2>Featured Products</h2>
                <div className="controls">
                    <button
                        className="refresh-btn"
                        onClick={loadProducts}
                        disabled={loading}
                    >
                        {loading ? 'Refreshing...' : 'Refresh Products'}
                    </button>
                    <select value={sortOrder} onChange={handleSortChange}>
                        <option value="default">Sort by</option>
                        <option value="lowToHigh">Price: Low to High</option>
                        <option value="highToLow">Price: High to Low</option>
                    </select>
                </div>
            </div>

            <div className="products-grid">
                {products.map(product => (
                    <ProductCard
                        key={product.product}
                        product={product}
                        onSelect={handleProductSelect}
                    />
                ))}
            </div>
        </div>
    );
};

export default Dashboard;