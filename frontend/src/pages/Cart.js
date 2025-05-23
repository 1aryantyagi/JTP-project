// src/pages/Cart.js
import React from 'react';
import { useCart } from '../contexts/CartContext';
import './Cart.css';

const Cart = () => {
    const { cartItems, removeFromCart, cartTotal } = useCart();

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
                    </>
                )}
            </div>
        </div>
    );
};

export default Cart;