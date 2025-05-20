// App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Components
const Login = ({ setLoggedIn }) => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });

  const handleLogin = (e) => {
    e.preventDefault();
    // Simple mock authentication
    setLoggedIn(true);
  };

  return (
    <div className="login-container">
      <h2>Product Recommendations</h2>
      <form onSubmit={handleLogin}>
        <input
          type="text"
          placeholder="Username"
          value={credentials.username}
          onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
        />
        <input
          type="password"
          placeholder="Password"
          value={credentials.password}
          onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
        />
        <button type="submit">Login</button>
      </form>
    </div>
  );
};

const ProductCard = ({ product, onRecommend, isSelected = false }) => {
  return (
    <div className={`product-card ${isSelected ? 'selected' : ''}`}>
      <h3>{product.product}</h3>
      <p><strong>Category:</strong> {product.category.join(', ')}</p>
      <p><strong>Sub-category:</strong> {product.sub_category.join(', ')}</p>
      <p><strong>Brand:</strong> {product.brand}</p>
      <p><strong>Price:</strong> ₹{product.sale_price}</p>
      {product.description && <p><strong>Description:</strong> {product.description}</p>}
      {!isSelected && (
        <button onClick={() => onRecommend(product.product)}>
          View Recommendations
        </button>
      )}
    </div>
  );
};

const Dashboard = ({ loggedIn }) => {
  const [products, setProducts] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchRandomProducts = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/random_products');
      setProducts(response.data.products);
      setRecommendations([]);
      setSelectedProduct(null);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async (productName) => {
    try {
      setLoading(true);
      const response = await axios.get(
        `http://localhost:8000/recommend/${encodeURIComponent(productName)}`
      );
      const selected = products.find(p => p.product === productName);
      setSelectedProduct(selected);
      setRecommendations(response.data.recommendations);
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      setRecommendations([]);
      setSelectedProduct(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (loggedIn) fetchRandomProducts();
  }, [loggedIn]);

  if (!loggedIn) return <Navigate to="/" />;

  return (
    <div className="dashboard">
      <div className="header">
        <h1>Product Dashboard</h1>
        <button className="refresh-btn" onClick={fetchRandomProducts}>
          Refresh Products
        </button>
      </div>

      {loading ? (
        <div className="loader">Loading...</div>
      ) : (
        <>
          {/* Selected Product and Recommendations Section */}
          {selectedProduct && (
            <div className="top-section">
              <div className="selected-product">
                <h2>Selected Product</h2>
                <ProductCard product={selectedProduct} isSelected />
              </div>

              <div className="recommendations">
                <h2>Recommended Products</h2>
                <div className="product-grid">
                  {recommendations.map((product) => (
                    <ProductCard key={product.product} product={product} />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Random Products Grid */}
          <div className="all-products">
            <h2>{selectedProduct ? 'Other Products' : 'All Products'}</h2>
            <div className="product-grid">
              {products.map((product) => (
                <ProductCard
                  key={product.product}
                  product={product}
                  onRecommend={fetchRecommendations}
                />
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Main App Component
export default function App() {
  const [loggedIn, setLoggedIn] = useState(false);

  return (
    <Router>
      <Routes>
        <Route
          path="/"
          element={loggedIn ? <Navigate to="/dashboard" /> : <Login setLoggedIn={setLoggedIn} />}
        />
        <Route path="/dashboard" element={<Dashboard loggedIn={loggedIn} />} />
      </Routes>
    </Router>
  );
}