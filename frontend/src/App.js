import React, { useEffect } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  Outlet,
  useNavigate
} from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { CartProvider } from './contexts/CartContext';
import { ViewedProductsProvider } from './contexts/ViewedProductsContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Recommendations from './pages/Recommendations';
import Cart from './pages/Cart';
import Layout from './components/Layout';
import './App.css';

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <CartProvider>
          <ViewedProductsProvider>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/" element={<ProtectedRoute />}>
                <Route path="/" element={<Layout />}>
                  <Route index element={<Dashboard />} />
                  <Route
                    path="recommendations/:productId"
                    element={<Recommendations />}
                  />
                  <Route path="cart" element={<Cart />} />
                </Route>
              </Route>
            </Routes>
          </ViewedProductsProvider>
        </CartProvider>
      </AuthProvider>
    </Router>
  );
}

function parseJwt(token) {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );

    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

function ProtectedRoute() {
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      const decodedToken = parseJwt(token);
      if (decodedToken && decodedToken.exp * 1000 < Date.now()) {
        logout();
        navigate('/login');
      }
    }
  }, [token, logout, navigate]);

  return user ? <Outlet /> : <Navigate to="/login" />;
}