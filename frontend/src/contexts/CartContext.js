import { createContext, useState, useContext } from 'react';

const CartContext = createContext();

export const CartProvider = ({ children }) => {
    const [cartItems, setCartItems] = useState([]);

    const addToCart = (product) => {
        setCartItems(prev => [...prev, product]);
    };

    const removeFromCart = (productId) => {
        setCartItems(prev => prev.filter(item => item.product !== productId));
    };

    const cartTotal = cartItems.reduce((sum, item) => sum + item.sale_price, 0);

    return (
        <CartContext.Provider value={{ cartItems, addToCart, removeFromCart, cartTotal }}>
            {children}
        </CartContext.Provider>
    );
};

export const useCart = () => useContext(CartContext);