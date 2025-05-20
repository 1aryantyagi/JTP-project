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
      {product.description && (
        <p>
          <strong>Description:</strong>{' '}
          {product.description.split(' ').slice(0, 40).join(' ')}{product.description.split(' ').length > 40 ? '.......' : ''}
        </p>
      )}
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
  const [sortOrder, setSortOrder] = useState('default');
  const [recommendSortOrder, setRecommendSortOrder] = useState('default');

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

  const handleSortChange = (e) => {
    const order = e.target.value;
    setSortOrder(order);

    const sortFn = (a, b) => {
      if (order === 'lowToHigh') return a.sale_price - b.sale_price;
      if (order === 'highToLow') return b.sale_price - a.sale_price;
      return 0;
    };

    const sorted = [...products].sort(sortFn);
    setProducts(sorted);
  };

  const handleRecommendSortChange = (e) => {
    const order = e.target.value;
    setRecommendSortOrder(order);

    const sortFn = (a, b) => {
      if (order === 'lowToHigh') return a.sale_price - b.sale_price;
      if (order === 'highToLow') return b.sale_price - a.sale_price;
      return 0; // default
    };

    const sorted = [...recommendations].sort(sortFn);
    setRecommendations(sorted);
  };

  useEffect(() => {
    if (recommendations.length > 0) {
      const sortFn = (a, b) => {
        if (recommendSortOrder === 'lowToHigh') return a.sale_price - b.sale_price;
        if (recommendSortOrder === 'highToLow') return b.sale_price - a.sale_price;
        return 0; // default
      };

      const sorted = [...recommendations].sort(sortFn);
      setRecommendations(sorted);
    }
  }, [recommendSortOrder]);

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

                {/* Sorting dropdown for recommendations */}
                <div className="sort-section">
                  <label htmlFor="recommend-sort">Sort by Price:</label>
                  <select
                    id="recommend-sort"
                    value={recommendSortOrder}
                    onChange={handleRecommendSortChange}
                  >
                    <option value="default">Default</option>
                    <option value="lowToHigh">Low to High</option>
                    <option value="highToLow">High to Low</option>
                  </select>
                </div>

                <div className="product-grid">
                  {recommendations.map((product) => (
                    <ProductCard
                      key={product.product}
                      product={product}
                      onRecommend={fetchRecommendations}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Sorting based in price */}
          <div className="sort-section">
            <label htmlFor="sort">Sort by Price:</label>
            <select id="sort" value={sortOrder} onChange={handleSortChange}>
              <option value="default">Default</option>
              <option value="lowToHigh">Low to High</option>
              <option value="highToLow">High to Low</option>
            </select>
          </div>

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