import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ProductCard from '../components/ProductCard';
import { fetchProductRecommendations } from '../services/api';
import { useViewedProducts } from '../contexts/ViewedProductsContext';
import './Recommendations.css';

const Recommendations = () => {
    const { productId } = useParams();
    const navigate = useNavigate();
    const [recommendations, setRecommendations] = useState([]);
    const [selectedProduct, setSelectedProduct] = useState(null);
    const [loading, setLoading] = useState(true);
    const [sortOrder, setSortOrder] = useState('default');
    const { viewedProducts } = useViewedProducts();

    useEffect(() => {
        const loadRecommendations = async () => {
            setLoading(true);
            setRecommendations([]);
            setSelectedProduct(null);

            try {
                const response = await fetchProductRecommendations(productId);
                setSelectedProduct(response.data.selected_product);
                setRecommendations(response.data.recommendations);
            } catch (error) {
                console.error('Error loading recommendations:', error);
            } finally {
                setLoading(false);
            }
        };

        loadRecommendations();
    }, [productId]);

    const handleSortChange = (e) => {
        const order = e.target.value;
        setSortOrder(order);

        const sorted = [...recommendations].sort((a, b) => {
            const priceA = parseFloat(a.sale_price);
            const priceB = parseFloat(b.sale_price);

            if (order === 'lowToHigh') return priceA - priceB;
            if (order === 'highToLow') return priceB - priceA;
            return 0;
        });

        setRecommendations(sorted);
    };

    const reversedViewedProducts = [...viewedProducts].reverse();

    return (
        <div className="recommendations-page">
            <div className="viewed-products-sidebar">
                <h3>Recently Viewed</h3>
                {reversedViewedProducts.length > 0 ? (
                    reversedViewedProducts.map((product) => (
                        <div
                            key={product.product}
                            className="viewed-product"
                            onClick={() => navigate(`/recommendations/${product.product}`)}
                        >
                            <div className="viewed-product-name">{product.product}</div>
                            <div className="viewed-product-price">₹{product.sale_price}</div>
                        </div>
                    ))
                ) : (
                    <div className="empty-viewed">No recently viewed items</div>
                )}
            </div>

            {/* Main Content */}
            <div className="main-content">
                <div className="recommendations-section">
                    <div className="section-header">
                        <h2>Recommended Products</h2>
                        <select
                            value={sortOrder}
                            onChange={handleSortChange}
                            disabled={loading}
                        >
                            <option value="default">Sort By</option>
                            <option value="lowToHigh">Price: Low to High</option>
                            <option value="highToLow">Price: High to Low</option>
                        </select>
                    </div>

                    {loading ? (
                        <div className="loading-indicator">Loading recommendations...</div>
                    ) : (
                        <div className="recommendations-grid">
                            {recommendations.map(product => (
                                <ProductCard key={product.product} product={product} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Recommendations;