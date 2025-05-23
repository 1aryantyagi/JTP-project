import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../contexts/CartContext';
import './ProductCard.css';

const ProductCard = ({ product }) => {
    const navigate = useNavigate();
    const { addToCart } = useCart();

    return (
        <div className="product-card">
            <div className="product-image">
                <img
                    src={product.image || "/images/default-product.jpg"}
                    alt={product.product}
                />
            </div>
            <div className="product-info">
                {/* Ensure product name is rendered */}
                <h3 className="product-name">{product.product}</h3>
                <p className="product-brand">{product.brand}</p>
                <p className="product-price">₹{product.sale_price}</p>
                <div className="product-actions">
                    <button
                        className="primary-btn"
                        onClick={() => navigate(`/recommendations/${product.product}`)}
                    >
                        View Recommendations
                    </button>
                    <button
                        className="secondary-btn"
                        onClick={() => addToCart(product)}
                    >
                        Add to Cart
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ProductCard;