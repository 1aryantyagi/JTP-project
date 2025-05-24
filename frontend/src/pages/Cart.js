import React, { useState, useEffect } from 'react';
import { useCart } from '../contexts/CartContext';
import ProductCard from '../components/ProductCard';
import { fetchCartRecommendations } from '../services/api';
import './Cart.css';

const Cart = () => {
    const { cartItems, removeFromCart, cartTotal } = useCart();
    const [cartRecommendations, setCartRecommendations] = useState([]);
    const [recLoading, setRecLoading] = useState(false);
    const [recError, setRecError] = useState('');

    useEffect(() => {
        if (cartItems.length > 0) {
            setRecLoading(true);
            setRecError('');
            const productNames = cartItems.map(item => item.product);

            fetchCartRecommendations(productNames)
                .then(response => {
                    setCartRecommendations(response.data.recommendations);
                    setRecLoading(false);
                })
                .catch(error => {
                    setRecError('Failed to load recommendations');
                    setRecLoading(false);
                });
        } else {
            setCartRecommendations([]);
        }
    }, [cartItems]);

    return (
        <div className="cart-page">
            <h2>Your Shopping Cart</h2>
            <div className="cart-container">
                {cartItems.length === 0 ? (
                    <div className="empty-cart">Your cart is empty</div>
                ) : (
                    <>
                        <div className="cart-items">
                            {cartItems.map((item, index) => (
                                <div key={index} className="cart-item">
                                    <div className="item-info">
                                        <h4>{item.product}</h4>
                                        <p>₹{item.sale_price}</p>
                                    </div>
                                    <button
                                        className="remove-btn"
                                        onClick={() => removeFromCart(item.product)}
                                    >
                                        Remove
                                    </button>
                                </div>
                            ))}
                        </div>
                        <div className="cart-summary">
                            <div className="total-amount">
                                <span>Total:</span>
                                <span>₹{cartTotal.toFixed(2)}</span>
                            </div>
                            <button className="checkout-btn">
                                Proceed to Checkout
                            </button>
                        </div>

                        <div className="cart-recommendations">
                            <h3>Frequently Bought Together</h3>
                            {recLoading && (
                                <div className="loader">
                                    <div className="loading-spinner"></div>
                                    Loading recommendations...
                                </div>
                            )}
                            {recError && (
                                <div className="error-message">{recError}</div>
                            )}
                            {!recLoading && !recError && (
                                <div className="recommendations-grid">
                                    {cartRecommendations.map(product => (
                                        <ProductCard
                                            key={product.product}
                                            product={product}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default Cart;