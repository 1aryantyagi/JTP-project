// frontend/src/contexts/ViewedProductsContext.js
import { createContext, useState, useContext } from 'react';

const ViewedProductsContext = createContext();

export const ViewedProductsProvider = ({ children }) => {
    const [viewedProducts, setViewedProducts] = useState([]);

    const addViewedProduct = (product) => {
        setViewedProducts(prev => [
            ...prev.filter(p => p.product !== product.product),
            product
        ].slice(-5)); // Keep last 5 unique products
    };

    return (
        <ViewedProductsContext.Provider value={{ viewedProducts, addViewedProduct }}>
            {children}
        </ViewedProductsContext.Provider>
    );
};

export const useViewedProducts = () => useContext(ViewedProductsContext);